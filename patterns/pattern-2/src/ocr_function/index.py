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
from idp_common.models import Document, Status, Page

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
        Dict with document including OCR results
    """       
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get document from event
    document = Document.from_dict(event["document"])
    
    input_bucket = document.input_bucket
    output_bucket = document.output_bucket
    object_key = document.input_key
    
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
    ocr_result = service.process_document(
        pdf_content=pdf_content,
        output_bucket=output_bucket,
        prefix=object_key
    )
    
    # Transfer OCR result to our Document object
    document.num_pages = ocr_result.num_pages
    document.metering.update(ocr_result.metering)
    document.status = Status.OCR_COMPLETED
    
    # Convert OCR pages to our Page model
    for page_id, ocr_page in ocr_result.pages.items():
        document.pages[page_id] = Page(
            page_id=page_id,
            image_uri=ocr_page.image_uri,
            raw_text_uri=ocr_page.raw_text_uri,
            parsed_text_uri=ocr_page.parsed_text_uri,
            tables=ocr_page.tables,
            forms=ocr_page.forms
        )
    
    t2 = time.time()
    logger.info(f"Time taken to process all {document.num_pages} pages: {t2-t1:.2f} seconds")
    logger.info(f"Finished processing {object_key} ({document.num_pages} pages) - output written to s3://{output_bucket}/{object_key}/")
    
    # Return the document as a dict - it will be passed to the next function
    response = {
        "document": document.to_dict()
    }
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response