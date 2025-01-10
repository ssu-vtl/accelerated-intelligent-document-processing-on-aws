# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import concurrent.futures
import time
import boto3
import json
import os
import io
import fitz  # PyMuPDF
from textractor.parsers import response_parser
import logging
from botocore.config import Config

print("Boto3 version: ", boto3.__version__)

region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 20))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
adaptive_config = Config(
    retries={'max_attempts': 100, 'mode': 'adaptive'},
    max_pool_connections=MAX_WORKERS*3
)
s3_client = boto3.client('s3', region_name=region, config=adaptive_config)
textract_client = boto3.client('textract', region_name=region, config=adaptive_config)
cloudwatch_client = boto3.client('cloudwatch', config=adaptive_config)

def put_metric(name, value, unit='Count', dimensions=None):
    dimensions = dimensions or []
    logger.info(f"Publishing metric {name}: {value}")
    try:
        cloudwatch_client.put_metric_data(
            Namespace=f'{METRIC_NAMESPACE}',
            MetricData=[{
                'MetricName': name,
                'Value': value,
                'Unit': unit,
                'Dimensions': dimensions
            }]
        )
    except Exception as e:
        logger.error(f"Error publishing metric {name}: {e}")

def process_single_page(page_index, pdf_document, working_bucket, prefix):
    t0 = time.time()
    page_number = page_index + 1
    
    page = pdf_document.load_page(page_index)
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("jpeg")
    
    # Upload image
    image_key = f"{prefix}/images/page_{page_number:04d}.jpg"
    s3_client.upload_fileobj(io.BytesIO(img_bytes), working_bucket, image_key)        
    t1 = time.time()
    logger.info(f"Time taken for image conversion (page {page_number}): {t1-t0:.6f} seconds")
    
    # Process with Textract
    textract_result = textract_client.detect_document_text(Document={"Bytes": img_bytes})
    
    # Store raw Textract response
    text_key = f"{prefix}/text_raw/page_{page_number:04d}.json"
    s3_client.put_object(
        Bucket=working_bucket,
        Key=text_key,
        Body=json.dumps(textract_result),
        ContentType='application/json'
    )

    # Store text from parsed Textract response
    parsed_result = response_parser.parse(textract_result)
    text_key = f"{prefix}/text_parsed/page_{page_number:04d}.json"
    s3_client.put_object(
        Bucket=working_bucket,
        Key=text_key,
        Body=json.dumps({"text": parsed_result.text}),
        ContentType='application/json'
    )

    t2 = time.time()
    logger.info(f"Time taken for Textract (page {page_number}): {t2-t1:.6f} seconds")
    
    return True

def get_document_text(pdf_content, working_bucket, prefix, max_workers = MAX_WORKERS):
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    num_pages = len(pdf_document)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_page = {
            executor.submit(process_single_page, i, pdf_document, working_bucket, prefix): i 
            for i in range(num_pages)
        }
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_index = future_to_page[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing page index {page_index}, page number {page_index + 1}: {str(e)}")
                raise
    
    pdf_document.close()
    return num_pages

def handler(event, context):        
    logger.info(f"Event: {json.dumps(event)}")
    input_bucket = event.get("input").get("detail").get("bucket").get("name")
    working_bucket = event.get("working_bucket")

    object_key = event.get("input").get("detail").get("object").get("key")
    # Get the PDF from S3
    t0 = time.time()
    response = s3_client.get_object(Bucket=input_bucket, Key=object_key)
    pdf_content = response['Body'].read()
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")
    # OCR the pages
    num_pages = get_document_text(pdf_content, working_bucket, prefix=object_key)
    logger.info(f"Finished processing {object_key} ({num_pages} pages) - output pages written to s3://{working_bucket}/{object_key}/")   
    response = {
        "input_bucket": input_bucket, 
        "object_key": object_key,
        "working_bucket": working_bucket,
        "working_prefix": object_key, 
        "num_pages": num_pages}
    return response 