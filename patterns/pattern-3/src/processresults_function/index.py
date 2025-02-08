# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.
import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, List
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def get_sections(object_bucket: str, object_key: str) -> List[Dict[str, Any]]:
    sections = []
    custom_output_prefix = f"{object_key}/custom_output/"
    
    try:
        # List all section folders
        response = s3_client.list_objects_v2(
            Bucket=object_bucket,
            Prefix=custom_output_prefix,
            Delimiter='/'
        )
        
        # Process each section folder
        for prefix in response.get('CommonPrefixes', []):
            section_path = prefix.get('Prefix')
            if not section_path:
                continue
                
            # Extract section ID from path
            section_id = section_path.rstrip('/').split('/')[-1]
            
            # Get the result.json file
            result_path = f"{section_path}result.json"
            try:
                result_obj = s3_client.get_object(
                    Bucket=object_bucket,
                    Key=result_path
                )
                result_data = json.loads(result_obj['Body'].read().decode('utf-8'))
                
                # Extract required fields
                doc_class = result_data.get('document_class', {}).get('type', '')
                page_indices = result_data.get('split_document', {}).get('page_indices', [])
                
                if page_indices:
                    page_ids = page_indices
                else:
                    page_ids = []
                
                # Construct section object
                section = {
                    "Id": section_id,
                    "PageIds": page_ids,
                    "Class": doc_class,
                    "OutputJSONUri": f"s3://{object_bucket}/{result_path}"
                }
                sections.append(section)
                
            except ClientError as e:
                logger.error(f"Failed to retrieve result.json for section {section_id}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in result.json for section {section_id}: {e}")
                continue
                
        logger.info(f"Retrieved {len(sections)} sections for document {object_key}")
        return sections
        
    except ClientError as e:
        logger.error(f"Failed to list sections in S3: {e}")
        raise

def get_pages(object_bucket: str, object_key: str) -> List[Dict[str, Any]]:
    pages = []
    custom_output_prefix = f"{object_key}/standard_output/"
    
    try:
        # List all page folders
        response = s3_client.list_objects_v2(
            Bucket=object_bucket,
            Prefix=custom_output_prefix,
            Delimiter='/'
        )
        
        # Process each page folder
        for prefix in response.get('CommonPrefixes', []):
            page_path = prefix.get('Prefix')
            if not page_path:
                continue
                
            # Extract section ID from path
            page_id = page_path.rstrip('/').split('/')[-1]
            
            # Get the result.json file
            result_path = f"{page_path}result.json"
            try:
                result_obj = s3_client.get_object(
                    Bucket=object_bucket,
                    Key=result_path
                )
                result_data = json.loads(result_obj['Body'].read().decode('utf-8'))
                
                # Extract required fields
                doc_class = result_data.get('document_class', {}).get('type', '')
                page_indices = result_data.get('split_document', {}).get('page_indices', [])
                
                if page_indices:
                    page_ids = page_indices
                else:
                    page_ids = []
                
                # Construct section object
                page = {
                    "Id": page_id,
                    "Class": doc_class,
                    "ImageUri": None,
                    "TextUri": f"s3://{object_bucket}/{result_path}"
                }
                pages.append(page)

                
            except ClientError as e:
                logger.error(f"Failed to retrieve result.json for pages {page_id}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in result.json for pages {page_id}: {e}")
                continue
                
        logger.info(f"Retrieved {len(pages)} pages for document {object_key}")
        return pages
        
    except ClientError as e:
        logger.error(f"Failed to list sections in S3: {e}")
        raise


def copy_s3_objects(source_bucket, source_prefix, output_bucket, object_key):
    """
    Copy objects from a source S3 location to a destination S3 location.
    """
    copied_files = 0
    try:
        # List all objects in source location using pagination
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=source_bucket,
            Prefix=source_prefix
        )

        # Process each object in the pages
        for page in page_iterator:
            if not page.get('Contents'):
                continue
                
            for obj in page['Contents']:
                source_key = obj['Key']
                relative_path = source_key[len(source_prefix):].lstrip('/')
                dest_key = f"{object_key}/{relative_path}"
                s3_client.copy_object(
                    CopySource={'Bucket': source_bucket, 'Key': source_key},
                    Bucket=output_bucket,
                    Key=dest_key,
                    ContentType='application/json',
                    MetadataDirective='REPLACE'
                )
                copied_files += 1
                
        logger.info(f"Successfully copied {copied_files} files")
        return copied_files
        
    except Exception as e:
        logger.error(f"Error copying files: {str(e)}")
        raise

def handler(event, context):
    """
        The Output must observe the structure below.. it is consumed by the GenAIDP parent stack workflow tracker to update job status/UI etc: 
            {
                'Sections': [
                    {
                        "Id": <ID>,
                        "PageIds": [<PAGEID>, ...],
                        "Class": <CLASS>,
                        "OutputJSONUri": <S3_URI>
                    }
                ],
                'Pages': [
                    "Id": <ID>,
                    "Class": <CLASS>,
                    "RawTextUri": <S3_URI>,
                    "ParsedTextUri": <S3_URI>,
                    "ImageUri": <S3_URI>
                ],
                'PageCount': <NUMBER OF PAGES IN ORIGINAL INPUT DOC>
            }
    """
    logger.info(f"Processing event: {json.dumps(event)}")
    
    # Extract required information
    output_bucket = event['output_bucket']
    object_key = event['BDAResponse']['job_detail']['input_s3_object']['name']
    source_bucket = event['BDAResponse']['job_detail']['output_s3_location']['s3_bucket']
    source_prefix = event['BDAResponse']['job_detail']['output_s3_location']['name']
    
    logger.info(f"Source bucket: {source_bucket}, prefix: {source_prefix}")
    logger.info(f"Destination bucket: {output_bucket}, base path: {object_key}")

    copied_count = copy_s3_objects(
        source_bucket,
        source_prefix,
        output_bucket,
        object_key
    )
    logger.info(f"Successfully copied {copied_count} files")
   
    # now get the document sections and pages from the BDA output
    sections = get_sections(output_bucket, object_key)
    pages = get_pages(output_bucket, object_key)
    
    statemachine_output = {
        "Sections": sections,
        "Pages": pages,
        "PageCount": len(pages)
    }

    return statemachine_output
        
