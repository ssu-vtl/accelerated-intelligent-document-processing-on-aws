"""
Classification function that processes documents and classifies them using LLMs.
Uses the idp_common.classification package for classification functionality.
"""

import json
import logging
import os
import time

from idp_common import classification, metrics, get_config
from idp_common.models import Document, Status

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
        Dict containing the updated Document object
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")
    
    # Extract document from the OCR result
    document = Document.from_dict(event["OCRResult"]["document"])
    
    if document.status != Status.OCR_COMPLETED:
        raise ValueError(f"Document is not in OCR_COMPLETED stage, current status: {document.status}")
    
    if not document.pages:
        raise ValueError("Document has no pages to classify")
    
    t0 = time.time()
    
    # Track pages processed
    total_pages = len(document.pages)
    metrics.put_metric('BedrockRequestsTotal', total_pages)
    
    # Initialize classification service
    service = classification.ClassificationService(
        region=region,
        max_workers=MAX_WORKERS,
        config=CONFIG
    )
    
    # Convert to the format expected by the classification service
    pages_dict = {
        page_id: {
            "rawTextUri": page.raw_text_uri,
            "parsedTextUri": page.parsed_text_uri,
            "imageUri": page.image_uri
        }
        for page_id, page in document.pages.items()
    }
    
    # Classify all pages
    classification_result = service.classify_pages(pages_dict)
    
    t1 = time.time()
    logger.info(f"Time taken for classification: {t1-t0:.2f} seconds")
    
    # Add sections and classifications to the document
    document.sections = []
    for section in classification_result.sections:
        # Create section object
        from idp_common.models import Section
        new_section = Section(
            section_id=section.section_id,
            classification=section.classification.doc_type,
            confidence=section.classification.confidence,
            page_ids=[p.page_id for p in section.pages]
        )
        document.sections.append(new_section)
        
        # Update page classifications
        for page in section.pages:
            if page.page_id in document.pages:
                document.pages[page.page_id].classification = page.classification.doc_type
                document.pages[page.page_id].confidence = page.classification.confidence
    
    # Update document status and metering
    document.status = Status.CLASSIFIED
    document.metering.update(classification_result.metadata.get("metering", {}))
    
    # Return document in a consistent envelope
    response = {
        "document": document.to_dict()
    }
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response