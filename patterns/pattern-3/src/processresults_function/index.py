# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    # Extract required information
    output_bucket = event['output_bucket']
    object_key = event['BDAResponse']['job_detail']['input_s3_object']['name']
    source_bucket = event['BDAResponse']['job_detail']['output_s3_location']['s3_bucket']
    source_prefix = event['BDAResponse']['job_detail']['output_s3_location']['name']
    
    logger.info(f"Source bucket: {source_bucket}, prefix: {source_prefix}")
    logger.info(f"Destination bucket: {output_bucket}, base path: {object_key}")
    
    # List all objects in source location
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
    
    copied_files = 0
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                source_key = obj['Key']
                relative_path = source_key[len(source_prefix):].lstrip('/')
                dest_key = f"{object_key}/{relative_path}"
                
                logger.debug(f"Copying {source_key} to {dest_key}")
                
                # Copy object
                s3_client.copy_object(
                    CopySource={'Bucket': source_bucket, 'Key': source_key},
                    Bucket=output_bucket,
                    Key=dest_key
                )
                copied_files += 1
    
    logger.info(f"Successfully copied {copied_files} files")
    return {
        'message': 'Files copied successfully',
        'source_bucket': source_bucket,
        'destination_bucket': output_bucket,
        'input_file': object_key,
        'files_copied': copied_files
    }
        
