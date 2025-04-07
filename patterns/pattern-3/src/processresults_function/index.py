import json
import logging
import datetime
import os
from urllib.parse import urlparse
from idp_common import s3, utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Consolidates the results from multiple extraction steps into a single output.
    """
    logger.info(f"Processing event: {json.dumps(event)}")

    sections=[]
    for result in event.get("extraction_results"):
        section = result.get("section")
        output_json_uri = section.get("outputJSONUri")
        class_type = section.get("class")
        
        # Create metadata file for each OutputJSONUri
        if output_json_uri:
            create_metadata_file(output_json_uri, class_type, 'section')
            
        sections.append({
            "Id": section.get("id"),
            "PageIds": section.get("page_ids"),
            "Class": class_type,
            "OutputJSONUri": output_json_uri
        })

    pages=[]
    for result in event.get("extraction_results"):
        for page in result.get("pages"):
            text_uri = page.get("rawTextUri")
            class_type = page.get("class")
            
            # Create metadata file for each TextUri
            if text_uri:
                create_metadata_file(text_uri, class_type, 'page')
                
            pages.append({
                "Id": page.get("page_id"),
                "Class": class_type,
                "TextUri": text_uri,
                "ImageUri": page.get("imageUri")
            })
    
    # Merge extraction metering into overall metering
    metering = event.get("metadata",{}).get("metering",{})
    for result in event.get("extraction_results"):
        result_metering = result.get("metering", {})
        metering = utils.merge_metering_data(metering, result_metering)

    statemachine_output = {
        "Sections": sections,
        "Pages": pages,
        "PageCount": event.get("metadata").get("num_pages"),
        "Metering": metering
    }

    return statemachine_output

def create_metadata_file(file_uri, class_type, file_type=None):
    """
    Creates a metadata file alongside the given URI file with the same name plus '.metadata.json'
    """
    try:
        # Parse the S3 URI to get bucket and key
        parsed_uri = urlparse(file_uri)
        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip('/')
        
        # Create the metadata key by adding '.metadata.json' to the original key
        metadata_key = f"{key}.metadata.json"
        
        # Determine the file type if not provided
        if file_type is None:
            if key.endswith('.json'):
                file_type = 'section'
            else:
                file_type = 'page'
        
        # Create metadata content
        metadata_content = {
            "metadataAttributes": {
                "DateTime": datetime.datetime.now().isoformat(),
                "Class": class_type,
                "FileType": file_type
            }
        }
        
        # Upload metadata file to S3 using common library
        s3.write_content(metadata_content, bucket, metadata_key, content_type='application/json')
        
        logger.info(f"Created metadata file at s3://{bucket}/{metadata_key}")
    except Exception as e:
        logger.error(f"Error creating metadata file for {file_uri}: {str(e)}")