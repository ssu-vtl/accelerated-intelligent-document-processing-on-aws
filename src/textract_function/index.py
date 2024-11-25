import boto3
import os
import io
import fitz  # PyMuPDF
from textractor.parsers import response_parser
import logging
import time
from botocore.config import Config


region = os.environ['AWS_REGION']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3', region_name=region)
# Initialize Textract client with adaptive retry to handle throttling
config = Config(
    retries = {
        'max_attempts': 100,
        'mode': 'adaptive'
    }
)
textract_client = boto3.client('textract', region_name=region, config=config)

def get_document_text(pdf_content):
    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    textract_pages = []

    # Iterate through each page, convert it to an image, and call Textract
    for page_number in range(len(pdf_document)):
        t0 = time.time()
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img_byte_arr = io.BytesIO(pix.tobytes(output="jpeg"))  # Convert pixmap to JPEG bytes
        img = io.BytesIO(img_byte_arr.getvalue())  # Prepare for sending to Textract
        t1 = time.time() 
        logger.info(f"Time taken for image conversion: {t1-t0:.6f} seconds")
        # Call Textract for each page image
        textract_result = textract_client.detect_document_text(Document={"Bytes": img.getvalue()})
        t2 = time.time()
        logger.info(f"Time taken for Textract: {t2-t1:.6f} seconds")
        textract_pages.append(response_parser.parse(textract_result))
    
    pdf_document.close()
    return textract_pages

def handler(event, context):
    # Extract bucket name and object key from the S3 event
        
    logger.info(f"Event: {event}")
    
    bucket_name = event.get("detail").get("bucket").get("name")
    object_key = event.get("detail").get("object").get("key")

    # Get the PDF object from S3
    t0 = time.time()
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    pdf_content = response['Body'].read()
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")

    response = get_document_text(pdf_content)

    document_str = ""
    for doc in response:
        document_str = document_str + doc.text
        
    logger.info(f"Document_text: {document_str}")   
    response = {"input_bucket_name": bucket_name, "input_object_key": object_key, "document_text": document_str}

    return response 