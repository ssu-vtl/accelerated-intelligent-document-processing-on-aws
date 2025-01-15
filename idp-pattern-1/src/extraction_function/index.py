# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import boto3
import os
import fitz  # PyMuPDF
import time
import json
import logging
import random
import io
from botocore.exceptions import ClientError
from prompt_catalog import DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT
from PIL import Image

print("Boto3 version: ", boto3.__version__)

# TODO - consider minimizing retries in lambda / maximize in Step Functions for cost efficiency.
MAX_RETRIES = 8 # avoid 900sec Lambda time out. 
INITIAL_BACKOFF = 2  # seconds
MAX_BACKOFF = 300   # 5 minutes

region = os.environ['AWS_REGION']
model_id = os.environ['EXTRACTION_MODEL_ID']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']
OCR_TEXT_ONLY = os.environ.get('OCR_TEXT_ONLY', 'false').lower() == 'true'

# Initialize clients without adaptive retry
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name=region)
cloudwatch_client = boto3.client('cloudwatch')
s3_client = boto3.client('s3', region_name=region)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def calculate_backoff(attempt):
    """Calculate exponential backoff with jitter"""
    backoff = min(MAX_BACKOFF, INITIAL_BACKOFF * (2 ** attempt))
    jitter = random.uniform(0, 0.1 * backoff)  # 10% jitter
    return backoff + jitter

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

def invoke_llm(page_images, system_prompts, task_prompt, document_text, attributes):
    inference_config = {"temperature": 0.5}
    if model_id.startswith("us.anthropic"):
        additional_model_fields = {"top_k": 200}
    else:
        additional_model_fields = None
    task_prompt = task_prompt.format(DOCUMENT_TEXT=document_text, ATTRIBUTES=attributes)
    system_prompt = [{"text": system_prompts}]
    content = [{"text": task_prompt}]

    # Claude currently supports max 20 image attachments
    # Per science team recommendation, we limit image attachments to 1st 20 pages.
    # TODO: Assess potential accuracy impact for longer documents, and if necessary consider alternate approaches 
    if len(page_images) > 20:
        page_images = page_images[:20] 
        logger.error(f"Number of pages in the document is greater than 20. Processing with only the first 20 pages")
    
    if page_images:
        logger.info(f"Attaching images to prompt, for {len(page_images)} pages.")
        for image in page_images:
            message = {"image": {
                "format": 'jpeg',
                "source": {"bytes": image}}}
            content.append(message)
    
    message = {
        "role": "user",
        "content": content
    }
    messages = [message]

    retry_count = 0
    last_exception = None
    request_start_time = time.time()

    # Track total requests
    put_metric('BedrockRequestsTotal', 1)

    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Bedrock request attempt {retry_count + 1}/{MAX_RETRIES} - "
                       f"model: {model_id}, "
                       f"inferenceConfig: {inference_config}, "
                       f"additionalFields: {additional_model_fields}")
            
            attempt_start_time = time.time()
            response = bedrock_client.converse(
                modelId=model_id,
                messages=messages,
                system=system_prompt,
                inferenceConfig=inference_config,
                additionalModelRequestFields=additional_model_fields
            )
            duration = time.time() - attempt_start_time
            
            logger.info(f"Bedrock request successful after {retry_count + 1} attempts. "
                       f"Duration: {duration:.2f}s")

            # Track successful requests and latency
            put_metric('BedrockRequestsSucceeded', 1)
            put_metric('BedrockRequestLatency', duration * 1000, 'Milliseconds')
            if retry_count > 0:
                put_metric('BedrockRetrySuccess', 1)

            # Track token usage
            if 'usage' in response:
                input_tokens = response['usage'].get('inputTokens', 0)
                output_tokens = response['usage'].get('outputTokens', 0)
                total_tokens = response['usage'].get('totalTokens', 0)
                put_metric('InputTokens', input_tokens)
                put_metric('OutputTokens', output_tokens)
                put_metric('TotalTokens', total_tokens)

            total_duration = time.time() - request_start_time
            put_metric('BedrockTotalLatency', total_duration * 1000, 'Milliseconds')

            entities = response['output']['message']['content'][0].get("text")
            return entities

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code in ['ThrottlingException', 'ServiceQuotaExceededException', 
                            'RequestLimitExceeded', 'TooManyRequestsException']:
                retry_count += 1
                put_metric('BedrockThrottles', 1)
                
                if retry_count == MAX_RETRIES:
                    logger.error(f"Max retries ({MAX_RETRIES}) exceeded. Last error: {error_message}")
                    put_metric('BedrockRequestsFailed', 1)
                    put_metric('BedrockMaxRetriesExceeded', 1)
                    raise
                
                backoff = calculate_backoff(retry_count)
                logger.warning(f"Bedrock throttling occurred (attempt {retry_count}/{MAX_RETRIES}). "
                             f"Error: {error_message}. "
                             f"Backing off for {backoff:.2f}s")
                
                time.sleep(backoff)
                last_exception = e
            else:
                logger.error(f"Non-retryable Bedrock error: {error_code} - {error_message}")
                put_metric('BedrockRequestsFailed', 1)
                put_metric('BedrockNonRetryableErrors', 1)
                raise

        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}", exc_info=True)
            put_metric('BedrockRequestsFailed', 1)
            put_metric('BedrockUnexpectedErrors', 1)
            raise

    if last_exception:
        raise last_exception


def get_text_content(bucket, text_path):
    """Read text content from a single S3 path"""
    try:
        # Extract key from s3:// URL
        key = text_path.replace(f"s3://{bucket}/", "")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = json.loads(response['Body'].read().decode('utf-8'))
        return content.get('text', '')
    except Exception as e:
        logger.error(f"Error reading text from {text_path}: {e}")
        raise

def get_image_content(bucket, image_path, target_width=951, target_height=1268):
    """Read and process a single image from S3"""
    try:
        # Extract key from s3:// URL
        key = image_path.replace(f"s3://{bucket}/", "")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        
        image = Image.open(io.BytesIO(image_data))
        current_width, current_height = image.size
        current_resolution = current_width * current_height
        target_resolution = target_width * target_height
        
        if current_resolution > target_resolution:
            logger.info(f"Downsizing image from {current_width}x{current_height}")
            image = image.resize((target_width, target_height))
        
        img_byte_array = io.BytesIO()
        image.save(img_byte_array, format="JPEG")
        return img_byte_array.getvalue()
        
    except Exception as e:
        logger.error(f"Error reading image from {image_path}: {e}")
        raise

def write_json_to_s3(json_string, bucket_name, object_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json_string,
        ContentType='application/json'
    )
    logger.info(f"JSON file successfully written to s3://{bucket_name}/{object_key}")

def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get parameters from event
    input_bucket = event.get("ClassificationResult", {}).get("input_bucket")
    working_bucket = event.get("ClassificationResult", {}).get("working_bucket")
    working_prefix = event.get("ClassificationResult", {}).get("working_prefix")
    object_key = event.get("ClassificationResult", {}).get("object_key")
    num_pages = event.get("ClassificationResult", {}).get("num_pages")
    class_label = event.get("ClassificationResult", {}).get("class_label")
    pages = event.get("ClassificationResult", {}).get("pages")
    output_bucket = event.get("output_bucket")
    output_prefix = object_key

    if not all([pages, working_bucket, class_label, output_bucket]):
        raise ValueError("Missing required parameters in event")

    # Sort pages by page number
    sorted_page_numbers = sorted(pages.keys(), key=int)
    start_page = int(sorted_page_numbers[0])
    end_page = int(sorted_page_numbers[-1])
    logger.info(f"Processing {len(sorted_page_numbers)} pages from {object_key}, class {class_label}: {start_page}-{end_page}")

    # Read document text from all pages in order
    t0 = time.time()
    document_texts = []
    for page_num in sorted_page_numbers:
        page_data = pages[page_num]
        text_path = page_data['textract_document_text_parsed_path']
        page_text = get_text_content(working_bucket, text_path)
        document_texts.append(page_text)
    
    document_text = '\n'.join(document_texts)
    t1 = time.time()
    logger.info(f"Time taken to read text content: {t1-t0:.2f} seconds")

    # Read page images if needed
    page_images = []
    for page_num in sorted_page_numbers:
        page_data = pages[page_num]
        image_path = page_data['image_path']
        image_content = get_image_content(working_bucket, image_path)
        page_images.append(image_content)
    
    t2 = time.time()
    logger.info(f"Time taken to read images: {t2-t1:.2f} seconds")

    # Load attributes
    with open("attributes.json", 'r') as file:
        attributes_list = json.load(file)

    # Process with LLM
    extracted_entities_str = invoke_llm(
        page_images,
        DEFAULT_SYSTEM_PROMPT,
        BASELINE_PROMPT,
        document_text,
        attributes_list
    )
    t3 = time.time()
    logger.info(f"Time taken by bedrock/claude: {t3-t2:.2f} seconds")

    # Write results
    output_key = f"{output_prefix}/{class_label}/Pages_{start_page}_to_{end_page}.json"
    write_json_to_s3(extracted_entities_str, output_bucket, output_key)
    
    # Track metrics
    put_metric('InputDocuments', 1)
    put_metric('InputDocumentPages', len(pages))
    
    result = {
        "input_bucket": input_bucket, 
        "object_key": object_key,
        "class_label": class_label,
        "num_pages": len(pages),
        "page_numbers": sorted_page_numbers,
        "extracted_entities": extracted_entities_str,
        "output_location": f"s3://{output_bucket}/{output_key}"
    }
    
    return result