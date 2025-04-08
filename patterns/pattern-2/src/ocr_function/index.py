"""
OCR function that processes PDFs and extracts text using AWS Textract.
Uses the idp_common.ocr package for OCR functionality.
"""

import json
import logging
import os
import time
import boto3

from idp_common import ocr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3
region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 20))

def handler(event, context): 
    """
    Lambda handler for OCR processing.

    Args:
        event: Event from Step Function with input file details
        context: Lambda context
        
    Returns:
        Dict with OCR results and metadata
    """       
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get input and output locations
    input_bucket = event.get("input").get("detail").get("bucket").get("name")
    output_bucket = event.get("output_bucket")
    object_key = event.get("input").get("detail").get("object").get("key")
    
    # Get the PDF from S3
    t0 = time.time()
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=input_bucket, Key=object_key)
    pdf_content = response['Body'].read()
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")
    
    # Initialize the OCR service
    service = ocr.OcrService(
        region=region,
        max_workers=MAX_WORKERS,
        enhanced_features=False  # Use basic OCR for now
    )
    
    # Process the document
    result = service.process_document(
        pdf_content=pdf_content,
        output_bucket=output_bucket,
        prefix=object_key
    )
    
    # Set input details in the result
    result.input_bucket = input_bucket
    result.input_key = object_key
    
    t2 = time.time()
    logger.info(f"Time taken to process all {result.num_pages} pages: {t2-t1:.2f} seconds")
    logger.info(f"Finished processing {object_key} ({result.num_pages} pages) - output written to s3://{output_bucket}/{object_key}/")
    
    # Convert to dictionary for API response
    response = result.to_dict()
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response