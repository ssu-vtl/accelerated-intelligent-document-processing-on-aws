import boto3
import os
import fitz  # PyMuPDF
import time
import json
import logging
import random
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

def invoke_claude(page_images, system_prompts, task_prompt, document_text, attributes):
    inference_config = {"temperature": 0.5}
    additional_model_fields = {"top_k": 200}
    task_prompt = task_prompt.format(DOCUMENT_TEXT=document_text, ATTRIBUTES=attributes)
    system_prompt = [{"text": system_prompts}]
    content = [{"text": task_prompt}]

    if len(page_images) > 20:
        page_images = page_images[:20] 
        logger.error(f"Number of pages in the document is greater than 20. Processing with only the first 20 pages")
    
    if page_images:
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


def get_document_page_images(pdf_content):
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    page_images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes(output="jpeg")
        
        # Add to images without resizing
        # page_images.append(img_bytes)

        # resize images
        image = Image.open(io.BytesIO(img_bytes))
        resized_image = image.resize((951, 1268))
        img_byte_array = io.BytesIO()
        resized_image.save(img_byte_array, format="JPEG")
        page_images.append(img_byte_array.getvalue())
    pdf_document.close()
    return page_images


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
    document_text = event.get("textract").get("document_text")
    input_bucket_name = event.get("textract").get("input_bucket_name")
    input_object_key = event.get("textract").get("input_object_key")
    output_bucket_name = event.get("output_bucket_name")
    output_object_key = input_object_key + ".json"
    # Get the PDF from S3
    t0 = time.time()
    response = s3_client.get_object(Bucket=input_bucket_name, Key=input_object_key)
    pdf_content = response['Body'].read()
    page_images = get_document_page_images(pdf_content)
    t1 = time.time()
    logger.info(f"Time taken for S3 GetObject: {t1-t0:.6f} seconds")
    with open("attributes.json", 'r') as file:
        attributes_list = json.load(file)
    t2 = time.time() 
    logger.info(f"Time taken to load attributes: {t2-t1:.6f} seconds")
    extracted_entites_str = invoke_claude(page_images, DEFAULT_SYSTEM_PROMPT, BASELINE_PROMPT, document_text, attributes_list)
    t3 = time.time() 
    logger.info(f"Time taken by bedrock/claude: {t3-t2:.6f} seconds")
    put_metric('InputDocuments', 1)
    put_metric('InputDocumentPages', len(page_images))
    write_json_to_s3(extracted_entites_str, output_bucket_name, output_object_key)
    t4 = time.time() 
    logger.info(f"Time taken to write extracted entities to S3: {t4-t3:.6f} seconds")
    return extracted_entites_str