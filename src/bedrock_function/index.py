import boto3
import os
import io
import fitz  # PyMuPDF
import time
from PIL import Image
import io
import base64
import json
from textractor.parsers import response_parser
import logging
from botocore.exceptions import ClientError
from prompt_catalog import DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT

region = "us-east-1"

# Initialize Textract client
textract_client = boto3.client('textract', region_name=region)
s3_client = boto3.client('s3', region_name=region)
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=region)
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
# model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def invoke_claude(images, system_prompts, task_prompt, document_text, attributes):
    """
    Sends a message to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        input text : The input message.
        input_image : The input image.

    Returns:
        response (JSON): The conversation that the model generated.

    """

    logger.info("Generating message with model %s", model_id)

    temperature = 0.5
    top_k = 200

    inference_config = {"temperature": temperature}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": top_k}

    task_prompt = task_prompt.format(DOCUMENT_TEXT = document_text, ATTRIBUTES = attributes)
    system_prompt = [{"text": system_prompts}]

    content = [{"text": task_prompt}]
    if images:
        for image in images: 
            message = {"image": {
                "format": 'jpeg',
                "source": {"bytes": image}}} 
            content.append(message)
    
    # content.append()

    message = {
        "role": "user",
        "content": content
    }

    messages = [message]

    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompt,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    entities = response['output']['message']['content'][0].get("text")

    return entities


def get_document_images(pdf_content):
    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    images = []

    # Iterate through each page, convert it to an image, and call Textract
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        
        # Convert Pixmap to a bytes object
        img_bytes = pix.tobytes(output="jpeg")

        images.append(img_bytes)
        
        # not needed to base 64 encode and resize 
        # # Create a BytesIO object and load it as a PIL image
        # image = Image.open(io.BytesIO(img_bytes))
        
        # # Resize the image
        # resized_image = image.resize((951, 1268))
        
        # # Save the resized image to a BytesIO object with reduced quality
        # output = io.BytesIO()
        # resized_image.save(output, 'jpeg', quality=40)
        
        # # Convert the image to base64
        # image_base64 = base64.b64encode(output.getvalue()).decode('utf-8')

        # images_base64.append(image_base64)
    
    pdf_document.close()
    return images


def write_json_to_s3(json_string, bucket_name, object_key):
    """
    Write a JSON object to a file in S3.

    Args:
        json_object (dict): The JSON object to write.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The S3 object key (path/filename.json).

    Returns:
        None
    """
    # Convert the Python dictionary to a JSON string

    # Upload the JSON string to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json_string,
        ContentType='application/json'
    )

    logger.info(f"JSON file successfully written to s3://{bucket_name}/{object_key}")


def handler(event, context):
    # Extract bucket name and object key from the S3 event
    
    start_time = time.time()
    
    logger.info(f"Event: {event}")
    
    document_text = event.get("text").get("document_text")

    bucket_name = event.get("text").get("bucket_name")
    object_key = event.get("text").get("object_key")
    
    output_bucket = event.get("outputBucket")

    output_object_key = "extracted-entities" + object_key.replace(".pdf", ".json")

    # Get the PDF object from S3
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    pdf_content = response['Body'].read()
    images = get_document_images(pdf_content)

    with open("attributes.json", 'r') as file:
        attributes_list = json.load(file)

    extracted_entites_str = invoke_claude(images, DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT, document_text, attributes_list)

    write_json_to_s3(extracted_entites_str, output_bucket, output_object_key)
    
    end_time = time.time()
    elapsed_time = start_time - end_time
    
    logger.info(f"Time taken for the detect text lambda: {elapsed_time:.6f} seconds")

    return None