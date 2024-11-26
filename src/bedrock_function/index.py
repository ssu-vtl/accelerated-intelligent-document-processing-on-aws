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
from botocore.config import Config
from prompt_catalog import DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT

region = os.environ['AWS_REGION']

# Initialize S3 client
s3_client = boto3.client('s3', region_name=region)
# Initialize Bedrock client with adaptive retry to handle throttling
config = Config(
    retries = {
        'max_attempts': 100,
        'mode': 'adaptive'
    }
)
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=region, config=config)

model_id = os.environ['EXTRACTION_MODEL_ID']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
   
    logger.info(f"Event: {event}")

    # Extract bucket name and object key from the event
    document_text = event.get("textract").get("document_text")
    input_bucket_name = event.get("textract").get("input_bucket_name")
    input_object_key = event.get("textract").get("input_object_key")
    output_bucket_name = event.get("output_bucket_name")
    output_object_key = input_object_key + ".json"

    # Get the PDF object from S3
    t0 = time.time()
    response = s3_client.get_object(Bucket=input_bucket_name, Key=input_object_key)
    pdf_content = response['Body'].read()
    images = get_document_images(pdf_content)
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")

    with open("attributes.json", 'r') as file:
        attributes_list = json.load(file)
    t2 = time.time() 
    logger.info(f"Time taken to load attributes: {t2-t1:.6f} seconds")

    extracted_entites_str = invoke_claude(images, DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT, document_text, attributes_list)
    t3 = time.time() 
    logger.info(f"Time taken by bedrock/claude: {t3-t2:.6f} seconds")

    write_json_to_s3(extracted_entites_str, output_bucket_name, output_object_key)
    t4 = time.time() 
    logger.info(f"Time taken to write extracted entities: {t4-t3:.6f} seconds")

    # return entities as step output
    return extracted_entites_str