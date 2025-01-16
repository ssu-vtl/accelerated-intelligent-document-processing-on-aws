import boto3
import os
import json
import time
import random
import logging
from botocore.exceptions import ClientError
from collections import defaultdict

print("Boto3 version: ", boto3.__version__)

# Retry configuration
MAX_RETRIES = 8 
INITIAL_BACKOFF = 2  # seconds
MAX_BACKOFF = 300   # 5 minutes

region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']

# Initialize clients
sm_client = boto3.client('sagemaker-runtime', region_name=region)
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

def classify_single_page(page_number, page_data):
    """Classify a single page using the UDOP model"""
    retry_count = 0
    last_exception = None
    
    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Classifying page {page_number}")
            
            # Prepare inference payload
            payload = {
                "textract": page_data['textract_document_text_raw_path'],
                "image": page_data['image_path']
            }
            logger.info(f"Payload: {payload}")
            
            # Invoke endpoint
            attempt_start_time = time.time()
            response = sm_client.invoke_endpoint(
                EndpointName=os.environ['SAGEMAKER_ENDPOINT_NAME'],
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            duration = time.time() - attempt_start_time
            
            # Parse response
            response_body = json.loads(response['Body'].read().decode())
            logger.info(f"Response body: {response_body}")
            
            # Log success metrics
            logger.info(f"Page {page_number} classification successful after {retry_count + 1} attempts. "
                       f"Duration: {duration:.2f}s")
            put_metric('ClassificationRequestsSucceeded', 1)
            put_metric('ClassificationLatency', duration * 1000, 'Milliseconds')
            if retry_count > 0:
                put_metric('ClassificationRetrySuccess', 1)
            
            # Return classification results along with page data
            return {
                'page_number': page_number,
                'classification': response_body['prediction'],
                'paths': page_data
            }     
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code in ['ThrottlingException', 'ServiceQuotaExceededException',
                            'RequestLimitExceeded', 'TooManyRequestsException']:
                retry_count += 1
                put_metric('ClassificationThrottles', 1)
                
                if retry_count == MAX_RETRIES:
                    logger.error(f"Max retries ({MAX_RETRIES}) exceeded for page {page_number}. "
                               f"Last error: {error_message}")
                    put_metric('ClassificationRequestsFailed', 1)
                    put_metric('ClassificationMaxRetriesExceeded', 1)
                    raise
                
                backoff = calculate_backoff(retry_count)
                logger.warning(f"Classification throttling occurred for page {page_number} "
                             f"(attempt {retry_count}/{MAX_RETRIES}). "
                             f"Error: {error_message}. "
                             f"Backing off for {backoff:.2f}s")
                
                time.sleep(backoff)
                last_exception = e
            else:
                logger.error(f"Non-retryable classification error for page {page_number}: "
                           f"{error_code} - {error_message}")
                put_metric('ClassificationRequestsFailed', 1)
                put_metric('ClassificationNonRetryableErrors', 1)
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error classifying page {page_number}: {str(e)}", 
                       exc_info=True)
            put_metric('ClassificationRequestsFailed', 1)
            put_metric('ClassificationUnexpectedErrors', 1)
            raise
            
    if last_exception:
        raise last_exception

def write_json_to_s3(json_string, bucket_name, object_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json_string,
        ContentType='application/json'
    )
    logger.info(f"JSON file successfully written to s3://{bucket_name}/{object_key}")

def group_consecutive_pages(results):
    """
    Group consecutive pages with the same classification.
    Returns a dictionary of class labels mapping to groups of consecutive pages.
    """
    # Sort results by page number to ensure proper consecutive grouping
    sorted_results = sorted(results, key=lambda x: x['page_number'])
    
    grouped_pages = defaultdict(dict)
    current_group = 1
    
    if not sorted_results:
        return grouped_pages
        
    # Initialize with first result
    current_class = sorted_results[0]['classification']
    current_pages = [sorted_results[0]]
    
    # Process remaining results
    for result in sorted_results[1:]:
        if result['classification'] == current_class:
            # Add to current group if same class
            current_pages.append(result)
        else:
            # Store current group and start new one
            grouped_pages[current_class][f"{current_class}_pagegroup_{current_group}"] = current_pages
            current_group += 1
            current_class = result['classification']
            current_pages = [result]
    
    # Store final group
    grouped_pages[current_class][f"{current_class}_pagegroup_{current_group}"] = current_pages
    
    return grouped_pages

def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get parameters from event
    input_bucket = event.get("OCRResult", {}).get("input_bucket")
    working_bucket = event.get("OCRResult", {}).get("working_bucket")
    working_prefix = event.get("OCRResult", {}).get("working_prefix")
    object_key = event.get("OCRResult", {}).get("object_key")
    num_pages = event.get("OCRResult", {}).get("num_pages")
    pages = event.get("OCRResult", {}).get("pages")

    if not all([input_bucket, working_bucket, working_prefix, object_key, num_pages, pages]):
        raise ValueError("Missing required parameters in event")

    t0 = time.time()
    
    # Track total classification requests
    total_pages = len(pages)
    put_metric('ClassificationRequestsTotal', total_pages)
    
    # Classify each page
    all_results = []
    for page_num, page_data in pages.items():
        result = classify_single_page(page_num, page_data)
        all_results.append(result)
    
    t1 = time.time()
    logger.info(f"Time taken for classification: {t1-t0:.2f} seconds")

    # Group consecutive pages with same classification
    pages_by_class = group_consecutive_pages(all_results)
    
    response = {
        "input_bucket": input_bucket, 
        "object_key": object_key,
        "working_bucket": working_bucket,
        "working_prefix": object_key, 
        "num_pages": num_pages,
        "pages_by_class": dict(pages_by_class)
    }

    # Write results to S3
    output_key = f"{working_prefix}/classification_results.json"
    write_json_to_s3(
        json.dumps(response),
        working_bucket,
        output_key
    )
    
    t2 = time.time()
    print("Response: ", response)
    logger.info(f"Time taken to sort and write results to S3: {t2-t1:.2f} seconds")

    return response