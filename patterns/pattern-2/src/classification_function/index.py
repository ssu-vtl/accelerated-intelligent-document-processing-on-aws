"""
Classification function that processes documents and classifies them using LLMs.
Uses the idp_common.classification package for classification functionality.
"""

import json
import logging
import os
import time

from idp_common import classification, metrics, utils, get_config

# Configuration
CONFIG = get_config()
region = os.environ['AWS_REGION']
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 20))

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler for document classification.
    
    Args:
        event: Event from Step Function with OCR results
        context: Lambda context
        
    Returns:
        Dict with classification results and metadata
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")
    
    # Get metadata and pages from OCR result
    metadata = event.get("OCRResult", {}).get("metadata")
    pages = event.get("OCRResult", {}).get("pages")
    
    if not all([metadata, pages]):
        raise ValueError("Missing required parameters in event")
    
    t0 = time.time()
    
    # Track pages processed
    total_pages = len(pages)
    metrics.put_metric('BedrockRequestsTotal', total_pages)
    
    # Initialize classification service
    service = classification.ClassificationService(
        region=region,
        max_workers=MAX_WORKERS,
        config=CONFIG
    )
    
    # Classify all pages
    classification_result = service.classify_pages(pages)
    
    t1 = time.time()
    logger.info(f"Time taken for classification: {t1-t0:.2f} seconds")
    
    # Merge incoming metering with classification metering
    incoming_metering = metadata.pop("metering", {})
    classification_metering = classification_result.metadata.get("metering", {})
    merged_metering = utils.merge_metering_data(classification_metering, incoming_metering)
    
    logger.info(f"Merged metering data: {json.dumps(merged_metering)}")
    
    # Update metadata with merged metering
    metadata["metering"] = merged_metering
    classification_result.metadata = metadata
    
    # Convert to dictionary for API response
    response = classification_result.to_dict()
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response