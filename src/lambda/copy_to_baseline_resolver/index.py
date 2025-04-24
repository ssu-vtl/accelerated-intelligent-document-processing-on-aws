import boto3
import os
import logging
import json
import concurrent.futures
import time
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fixed number of workers for I/O bound operations
# For S3 operations, this is more effective than dynamically calculating based on CPU
MAX_WORKERS = 20

# Minimum files per batch to avoid excessive batches with too few files
MIN_BATCH_SIZE = 5

def copy_s3_object(source_bucket, destination_bucket, object_key):
    """
    Copy a single S3 object from source to destination bucket
    """
    # Use the same S3 client for all operations in this function
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

def batch_copy_s3_objects(source_bucket, destination_bucket, object_keys):
    """
    Copy a batch of S3 objects from source to destination bucket
    
    Args:
        source_bucket: Source S3 bucket
        destination_bucket: Destination S3 bucket
        object_keys: List of object keys to copy
        
    Returns:
        Tuple of (successful_copies, failed_copies)
    """
    # Create a single client for all operations in this batch
    s3_client = boto3.client('s3', config=Config(
        max_pool_connections=min(len(object_keys), 50),
        retries={'max_attempts': 3}
    ))
    
    successful = []
    failed = []
    
    for key in object_keys:
        copy_source = {
            'Bucket': source_bucket,
            'Key': key
        }
        
        try:
            s3_client.copy_object(
                CopySource=copy_source,
                Bucket=destination_bucket,
                Key=key
            )
            successful.append(key)
        except Exception as e:
            logger.error(f"Error copying object {key}: {str(e)}")
            failed.append(key)
    
    return successful, failed

def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    start_time = time.time()

    try:
        object_key = event['arguments']['objectKey']
        
        # Get bucket names from environment variables
        source_bucket = os.environ['OUTPUT_BUCKET']
        destination_bucket = os.environ['EVALUATION_BASELINE_BUCKET']
        
        # Create S3 client with optimized configuration
        s3_client = boto3.client('s3', config=Config(
            max_pool_connections=MAX_WORKERS*2,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        ))
        
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
        
        total_objects = len(objects_to_copy)
        if total_objects == 0:
            return {
                'success': True,
                'message': f'No objects found under prefix {object_key}'
            }
            
        logger.info(f"Found {total_objects} objects to copy under prefix {object_key}")
        
        # Determine optimal batch size based on total files and available workers
        # Using max(workers, 1) to ensure we don't divide by zero
        workers_to_use = min(MAX_WORKERS, total_objects)
        
        # Calculate batch size - divide total files evenly among workers
        # but ensure at least MIN_BATCH_SIZE files per batch
        calculated_batch_size = max(total_objects // workers_to_use, MIN_BATCH_SIZE)
        
        # Prepare batches of files for workers to process
        batches = []
        for i in range(0, total_objects, calculated_batch_size):
            batch = objects_to_copy[i:i + calculated_batch_size]
            batches.append(batch)
        
        avg_batch_size = total_objects / len(batches) if batches else 0
        logger.info(f"Created {len(batches)} batches with average {avg_batch_size:.1f} files per batch")
        
        # Process batches in parallel with a fixed number of workers
        copied_count = 0
        failed_count = 0
        
        # Use only as many workers as we have batches, up to MAX_WORKERS
        max_workers = min(MAX_WORKERS, len(batches))
        logger.info(f"Using {max_workers} workers to process {len(batches)} batches ({total_objects} total files)")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit batches to thread pool
            future_to_batch = {
                executor.submit(batch_copy_s3_objects, source_bucket, destination_bucket, batch): batch 
                for batch in batches
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    successful, failed = future.result()
                    copied_count += len(successful)
                    failed_count += len(failed)
                    
                    # Log progress periodically
                    total_processed = copied_count + failed_count
                    if total_processed % 100 == 0 or total_processed == total_objects:
                        logger.info(f"Progress: {total_processed}/{total_objects} files processed")
                        
                except Exception as e:
                    logger.error(f"Exception in batch processing: {str(e)}")
                    # Assume all files in this batch failed
                    batch = future_to_batch[future]
                    failed_count += len(batch)

        total_count = copied_count + failed_count
        elapsed_time = time.time() - start_time
        logger.info(f'Copied {copied_count}/{total_count} files in {elapsed_time:.2f} seconds '
                   f'({copied_count/elapsed_time:.2f} files/sec)')
        
        if failed_count > 0:
            message = f'Copied {copied_count}/{total_count} files. {failed_count} files failed to copy.'
            success = False
        else:
            message = f'Successfully copied {copied_count} files under prefix {object_key} to baseline bucket'
            success = True
            
        return {
            'success': success,
            'message': message,
            'copied': copied_count,
            'failed': failed_count,
            'elapsed_seconds': elapsed_time
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
