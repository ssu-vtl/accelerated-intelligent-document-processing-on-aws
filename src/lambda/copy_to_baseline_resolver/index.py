import boto3
import os
import logging
import json
import concurrent.futures
import multiprocessing
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def copy_s3_object(source_bucket, destination_bucket, object_key):
    """
    Copy a single S3 object from source to destination bucket
    """
    s3_client = boto3.client('s3')
    copy_source = {
        'Bucket': source_bucket,
        'Key': object_key
    }
    
    try:
        s3_client.copy_object(
            CopySource=copy_source,
            Bucket=destination_bucket,
            Key=object_key
        )
        return True
    except Exception as e:
        logger.error(f"Error copying object {object_key}: {str(e)}")
        return False

def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        object_key = event['arguments']['objectKey']
        
        # Get bucket names from environment variables
        source_bucket = os.environ['OUTPUT_BUCKET']
        destination_bucket = os.environ['EVALUATION_BASELINE_BUCKET']
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # List all objects under the prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        operation_parameters = {
            'Bucket': source_bucket,
            'Prefix': object_key
        }

        # Collect all objects to copy
        objects_to_copy = []
        for page in paginator.paginate(**operation_parameters):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                objects_to_copy.append(obj['Key'])
        
        # Use ThreadPoolExecutor for parallel copying
        # Determine optimal number of workers based on available CPU resources
        # For I/O bound tasks like S3 operations, we can use more threads than CPU cores
        cpu_count = multiprocessing.cpu_count()
        # For I/O bound tasks, a multiplier of 4-5x CPU count is often effective
        optimal_workers = cpu_count * 5
        # Cap the number of workers to avoid overwhelming resources
        max_workers = min(optimal_workers, len(objects_to_copy), 100)
        
        logger.info(f"CPU count: {cpu_count}, using {max_workers} workers for {len(objects_to_copy)} objects")
        
        copied_count = 0
        failed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary of futures to their corresponding object keys
            future_to_key = {
                executor.submit(copy_s3_object, source_bucket, destination_bucket, key): key 
                for key in objects_to_copy
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    success = future.result()
                    if success:
                        copied_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Exception copying {key}: {str(e)}")
                    failed_count += 1

        total_count = copied_count + failed_count
        logger.info(f'Copied {copied_count}/{total_count} files under prefix {object_key} to baseline bucket')
        
        if failed_count > 0:
            message = f'Copied {copied_count}/{total_count} files. {failed_count} files failed to copy.'
            success = False
        else:
            message = f'Successfully copied {copied_count} files under prefix {object_key} to baseline bucket'
            success = True
            
        return {
            'success': success,
            'message': message
        }
        
    except ClientError as e:
        error_message = str(e)
        logger.error(f'Failed to copy files: {error_message}')
        return {
            'success': False,
            'message': f'Failed to copy files: {error_message}'
        }
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }
