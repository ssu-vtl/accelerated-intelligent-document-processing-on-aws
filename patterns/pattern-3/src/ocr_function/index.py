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
from idp_common import metrics, utils, s3

region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 20))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# For OCR, we need to use the boto3 clients directly with adaptive config
adaptive_config = Config(
    retries={'max_attempts': 100, 'mode': 'adaptive'},
    max_pool_connections=MAX_WORKERS*3
)
s3_client = boto3.client('s3', region_name=region, config=adaptive_config)
textract_client = boto3.client('textract', region_name=region, config=adaptive_config)

def put_metric(name, value, unit='Count', dimensions=None):
    metrics.put_metric(name, value, unit, dimensions, METRIC_NAMESPACE)

def process_single_page(page_index, pdf_document, output_bucket, prefix):
    t0 = time.time()
    page_id = page_index + 1
    
    page = pdf_document.load_page(page_index)
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("jpeg")
    
    # Upload image
    image_key = f"{prefix}/pages/{page_id}/image.jpg"
    s3.write_content(img_bytes, output_bucket, image_key, content_type='image/jpeg')    
    
    t1 = time.time()
    logger.info(f"Time taken for image conversion (page {page_id}): {t1-t0:.6f} seconds")
    
    # Process with Textract
    textract_result = textract_client.detect_document_text(Document={"Bytes": img_bytes})

    metering = {
        "textract/detect_document_text": {
            "pages": textract_result["DocumentMetadata"]["Pages"]
        }
    }
    
    # Store raw Textract response
    raw_text_key = f"{prefix}/pages/{page_id}/rawText.json"
    s3.write_content(textract_result, output_bucket, raw_text_key, content_type='application/json')

    # Store text from parsed Textract response
    parsed_text_key = f"{prefix}/pages/{page_id}/result.json"
    parsed_result = response_parser.parse(textract_result)
    s3.write_content({"text": parsed_result.text}, output_bucket, parsed_text_key, content_type='application/json')

    t2 = time.time()
    logger.info(f"Time taken for Textract (page {page_id}): {t2-t1:.6f} seconds")
    
    # Return paths and metering for this page
    return {
        "rawTextUri": f"s3://{output_bucket}/{raw_text_key}",
        "parsedTextUri": f"s3://{output_bucket}/{parsed_text_key}",
        "imageUri": f"s3://{output_bucket}/{image_key}",
        "metering": metering
    }

def get_document_text(pdf_content, output_bucket, prefix, max_workers = MAX_WORKERS):
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    num_pages = len(pdf_document)
    page_results = {}
    metering = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_page = {
            executor.submit(process_single_page, i, pdf_document, output_bucket, prefix): i 
            for i in range(num_pages)
        }
        
        for future in concurrent.futures.as_completed(future_to_page):
            page_index = future_to_page[future]
            try:
                result = future.result()
                page_metering = result.pop("metering", {})
                page_results[str(page_index + 1)] = result
                
                # Merge metering with common utility
                metering = utils.merge_metering_data(metering, page_metering)
            except Exception as e:
                logger.error(f"Error processing page index {page_index}, page number {page_index + 1}: {str(e)}")
                raise
    
    pdf_document.close()
    return num_pages, page_results, metering

def handler(event, context): 
    """
    Input event for new input object packet/document
    """       
    logger.info(f"Event: {json.dumps(event)}")
    input_bucket = event.get("input").get("detail").get("bucket").get("name")
    output_bucket = event.get("output_bucket")

    object_key = event.get("input").get("detail").get("object").get("key")
    
    # Get the PDF from S3
    t0 = time.time()
    
    # Use the boto3 S3 client directly here since we need raw binary content
    # and our s3 module is optimized for text/JSON
    response = s3_client.get_object(Bucket=input_bucket, Key=object_key)
    pdf_content = response['Body'].read()
    
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")
    
    # OCR the pages
    num_pages, page_results, metering = get_document_text(pdf_content, output_bucket, prefix=object_key)
    logger.info(f"Finished processing {object_key} ({num_pages} pages) - output pages written to s3://{output_bucket}/{object_key}/")   
    
    t2 = time.time()
    logger.info(f"Time taken to process all {num_pages} pages: {t2-t1:.2f} seconds")

    response = {
        "metadata": {
            "input_bucket": input_bucket, 
            "object_key": object_key,
            "output_bucket": output_bucket,
            "output_prefix": object_key, 
            "num_pages": num_pages,
            "metering": metering
        },
        "pages": page_results
    }
    return response