# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import os
import json
import time
import logging
from idp_common import metrics, get_config, extraction

CONFIG = get_config()

OCR_TEXT_ONLY = os.environ.get('OCR_TEXT_ONLY', 'false').lower() == 'true'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Input event for single document / section of given type
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")  
    
    # Get parameters from event
    metadata = event.get("metadata")
    section = event.get("section")
    output_bucket = event.get("output_bucket")   
    object_key = metadata.get("object_key")
    class_label = section.get("class")
    pages = section.get("pages")
    page_ids = [page['page_id'] for page in pages]
    
    # Initialize the extraction service
    extraction_service = extraction.ExtractionService(config=CONFIG)
    
    # Track metrics
    metrics.put_metric('InputDocuments', 1)
    metrics.put_metric('InputDocumentPages', len(pages))
    
    # Process the section using the extraction service
    t0 = time.time()
    result = extraction_service.extract_from_section(
        section=section,
        metadata=metadata,
        output_bucket=output_bucket
    )
    t1 = time.time()
    logger.info(f"Total extraction time: {t1-t0:.2f} seconds")
    
    # Create response object
    output_key = f"{object_key}/sections/{section['id']}/result.json"
    response = {
        "section": {
            "id": section['id'],
            "class": section['class'],
            "page_ids": page_ids,
            "outputJSONUri": result.output_uri or f"s3://{output_bucket}/{output_key}",
        },
        "pages": pages,
        "metering": result.metering
    }
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response