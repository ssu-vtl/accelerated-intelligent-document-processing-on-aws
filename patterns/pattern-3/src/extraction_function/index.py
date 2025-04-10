# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import os
import json
import time
import logging
from idp_common import metrics, get_config, extraction
from idp_common.models import Document, Section, Status

CONFIG = get_config()

OCR_TEXT_ONLY = os.environ.get('OCR_TEXT_ONLY', 'false').lower() == 'true'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Process a single section of a document for information extraction
    
    Args:
        event: Contains the section data and document metadata
        context: Lambda context
        
    Returns:
        Dict containing the extraction results for the section
    """
    logger.info(f"Event: {json.dumps(event)}")
    logger.info(f"Config: {json.dumps(CONFIG)}")
    
    # For Map state, we get just one section from the document
    # Extract the document from the event
    document = Document.from_dict(event.get("document", {}))
    section_data = event.get("section", {})
    
    # Find the section in the document
    section_id = section_data.get("section_id", "")
    
    # Get the current section from the document if it exists
    section = None
    for s in document.sections:
        if s.section_id == section_id:
            section = s
            break
    
    if not section:
        # Create a new section if not found
        section = Section(
            section_id=section_id,
            classification=section_data.get("classification", ""),
            page_ids=section_data.get("page_ids", [])
        )
    
    # Create the section in format expected by extraction service
    extraction_section = {
        "id": section.section_id,
        "class": section.classification,
        "pages": []
    }
    
    # Add pages to the section
    for page_id in section.page_ids:
        if page_id in document.pages:
            page = document.pages[page_id]
            extraction_section["pages"].append({
                "page_id": page.page_id,
                "rawTextUri": page.raw_text_uri,
                "parsedTextUri": page.parsed_text_uri,
                "imageUri": page.image_uri,
                "class": page.classification
            })
    
    # Create metadata from document
    metadata = {
        "input_bucket": document.input_bucket,
        "object_key": document.input_key,
        "output_bucket": document.output_bucket,
        "num_pages": document.num_pages
    }
    
    # Initialize the extraction service
    extraction_service = extraction.ExtractionService(config=CONFIG)
    
    # Track metrics
    metrics.put_metric('InputDocuments', 1)
    metrics.put_metric('InputDocumentPages', len(section.page_ids))
    
    # Process the section using the extraction service
    t0 = time.time()
    result = extraction_service.extract_from_section(
        section=extraction_section,
        metadata=metadata,
        output_bucket=document.output_bucket
    )
    t1 = time.time()
    logger.info(f"Total extraction time: {t1-t0:.2f} seconds")
    
    # Update section with extraction results
    section.extraction_result_uri = result.output_uri or f"s3://{document.output_bucket}/{document.input_key}/sections/{section.section_id}/result.json"
    
    # Update status for this section
    section_document = Document(
        id=document.id,
        input_bucket=document.input_bucket,
        input_key=document.input_key,
        output_bucket=document.output_bucket,
        status=Status.EXTRACTED,
        queued_time=document.queued_time,
        start_time=document.start_time,
        workflow_execution_arn=document.workflow_execution_arn,
        num_pages=document.num_pages,
        metering=result.metering or {}
    )
    
    # Include only this section in the result
    section_document.sections = [section]
    
    # Return section extraction result with the document
    # The state machine will later combine all section results
    response = {
        "section_id": section.section_id,
        "document": section_document.to_dict()
    }
    
    logger.info(f"Response: {json.dumps(response, default=str)}")
    return response