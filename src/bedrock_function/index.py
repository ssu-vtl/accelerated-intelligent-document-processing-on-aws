import boto3
import os
import fitz  # PyMuPDF
import time
import json
import logging
from botocore.config import Config
from prompt_catalog import DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT

region = os.environ['AWS_REGION']
model_id = os.environ['EXTRACTION_MODEL_ID']

# Initialize clients
adaptive_config = Config(retries={'max_attempts': 100, 'mode': 'adaptive'})
cloudwatch_client = boto3.client('cloudwatch')
s3_client = boto3.client('s3', region_name=region)
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=region, config=adaptive_config)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def put_metric(name, value, unit='Count', dimensions=None):
    dimensions = dimensions or []
    logger.info(f"Publishing metric {name}: {value}")
    try:
        cloudwatch_client.put_metric_data(
            Namespace='Custom/Bedrock',
            MetricData=[{
                'MetricName': name,
                'Value': value,
                'Unit': unit,
                'Dimensions': dimensions
            }]
        )
    except Exception as e:
        logger.error(f"Error publishing metric {name}: {e}")

def invoke_claude(images, system_prompts, task_prompt, document_text, attributes):
    inference_config = {"temperature": 0.5}
    additional_model_fields = {"top_k": 200}
    task_prompt = task_prompt.format(DOCUMENT_TEXT = document_text, ATTRIBUTES = attributes)
    system_prompt = [{"text": system_prompts}]
    content = [{"text": task_prompt}]
    if images:
        for image in images: 
            message = {"image": {
                "format": 'jpeg',
                "source": {"bytes": image}}} 
            content.append(message)
    message = {
        "role": "user",
        "content": content
    }
    messages = [message]
    logger.info(f"Bedrock Request - model {model_id}, inferenceConfig {inference_config} {additional_model_fields}", )
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompt,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )
    logger.info("Bedrock Response: %s", response)
    # Track token usage
    if 'usage' in response:
        input_tokens = response['usage'].get('inputTokens', 0)
        output_tokens = response['usage'].get('outputTokens', 0)
        put_metric('InputTokens', input_tokens)
        put_metric('OutputTokens', output_tokens)
    entities = response['output']['message']['content'][0].get("text")
    return entities


def get_document_images(pdf_content):
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes(output="jpeg")
        images.append(img_bytes)
    pdf_document.close()
    return images


def write_json_to_s3(json_string, bucket_name, object_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json_string,
        ContentType='application/json'
    )
    logger.info(f"JSON file successfully written to s3://{bucket_name}/{object_key}")


def handler(event, context):
    logger.info(f"Event: {event}")
    document_text = event.get("textract").get("document_text")
    input_bucket_name = event.get("textract").get("input_bucket_name")
    input_object_key = event.get("textract").get("input_object_key")
    output_bucket_name = event.get("output_bucket_name")
    output_object_key = input_object_key + ".json"
    # Get the PDF from S3
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
    logger.info(f"Time taken to write extracted entities to S3: {t4-t3:.6f} seconds")
    return extracted_entites_str