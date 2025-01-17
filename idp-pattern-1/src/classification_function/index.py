import boto3
import os
import json
import time
import random
import logging
from botocore.exceptions import ClientError
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

print("Boto3 version: ", boto3.__version__)

# Retry configuration
MAX_RETRIES = 8 
INITIAL_BACKOFF = 2  # seconds
MAX_BACKOFF = 300   # 5 minutes
MAX_WORKERS = 20     # Adjust based on your needs and endpoint capacity

region = os.environ['AWS_REGION']
METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']

# Initialize clients
sm_client = boto3.client('sagemaker-runtime', region_name=region)
cloudwatch_client = boto3.client('cloudwatch')
s3_client = boto3.client('s3', region_name=region)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add thread-safe metric publishing
metric_lock = Lock()

def calculate_backoff(attempt):
    """Calculate exponential backoff with jitter"""
    backoff = min(MAX_BACKOFF, INITIAL_BACKOFF * (2 ** attempt))
    jitter = random.uniform(0, 0.1 * backoff)  # 10% jitter
    return backoff + jitter

def put_metric(name, value, unit='Count', dimensions=None):
    dimensions = dimensions or []
    logger.info(f"Publishing metric {name}: {value}")
    with metric_lock:  # Ensure thread-safe metric publishing
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
    Group consecutive pages with the same classification into pagegroups.
    Returns a list of pagegroups, each containing an id, document_type, and pages.
    """
    # Sort results by page number to ensure proper consecutive grouping
    sorted_results = sorted(results, key=lambda x: x['page_number'])
    
    pagegroups = []
    current_group = 1
    
    if not sorted_results:
        return pagegroups
        
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
            pagegroups.append({
                'id': f"Class_{current_class}_Pagegroup_{current_group}",
                'document_type': current_class,
                'pages': current_pages
            })
            current_group += 1
            current_class = result['classification']
            current_pages = [result]
    
    # Store final group
    pagegroups.append({
        'id': f"{current_class}_pagegroup_{current_group}",
        'document_type': current_class,
        'pages': current_pages
    })
    
    return pagegroups

def classify_pages_concurrently(pages):
    """Classify multiple pages concurrently using a thread pool"""
    all_results = []
    futures = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all classification tasks
        for page_num, page_data in pages.items():
            future = executor.submit(classify_single_page, page_num, page_data)
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                logger.error(f"Error in concurrent classification: {str(e)}")
                raise
    
    return all_results

def handler(event, context):
    """
    Input event containing page level OCR and image data from OCR step:
    {
        "execution_arn": <ARN>,
        "output_bucket": <BUCKET>,
        "OCRResult": {
            "metadata": {
                "input_bucket": <BUCKET>,
                "object_key": <KEY>,
                "working_bucket": <BUCKET>,
                "working_prefix": <PREFIX>,
                "num_pages": <NUMBER OF PAGES IN ORIGINAL INPUT DOC>
            }
        },
        "pages": {
            <ID>: {
                        "textract_document_text_raw_path": <S3_URI>,
                        "textract_document_text_parsed_path": <S3_URI>,
                        "image_path": <S3_URI>
            }
        }
    }
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get parameters from event
    metadata = event.get("OCRResult", {}).get("metadata")
    pages = event.get("OCRResult", {}).get("pages")

    if not all([metadata, pages]):
        raise ValueError("Missing required parameters in event")

    t0 = time.time()
    
    # Track total classification requests
    total_pages = len(pages)
    put_metric('ClassificationRequestsTotal', total_pages)
    
    # Classify pages concurrently
    all_results = classify_pages_concurrently(pages)
    
    t1 = time.time()
    logger.info(f"Time taken for classification: {t1-t0:.2f} seconds")

    # Group consecutive pages with same classification
    pagegroups = group_consecutive_pages(all_results)
    
    response = {
        "metadata": metadata,
        "pagegroups": pagegroups
    }

    # Write results to S3
    output_key = f'{metadata["working_prefix"]}/classification_results.json'
    write_json_to_s3(
        json.dumps(response),
        metadata["working_bucket"],
        output_key
    )
    
    t2 = time.time()
    print("Response: ", response)
    logger.info(f"Time taken to sort and write results to S3: {t2-t1:.2f} seconds")

    return response