"""
Lambda function to summarize document content using the SummarizationService from idp_common.
"""
import json
import os
import logging
import time

# Import the SummarizationService from idp_common
from idp_common import get_config, summarization
from idp_common.models import Document, Status
from idp_common.appsync.service import DocumentAppSyncService

# Configuration
CONFIG = get_config()

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
# Get LOG_LEVEL from environment variable with INFO as default

def handler(event, context):
    """
    Lambda handler for document summarization using the SummarizationService.
    
    Args:
        event: Lambda event containing document data and configuration
        context: Lambda context
        
    Returns:
        Dictionary with the summarization result
    """
    logger.info(f"Processing event: {json.dumps(event)}")
    start_time = time.time()
    
    try:
        # Get required parameters
        document_dict = event.get('document', {})
        
        if not document_dict:
            raise ValueError("No document data provided")
        
        # Convert dict to Document object
        document = Document.from_dict(document_dict)
        
        # Update document status to SUMMARIZING
        document.status = Status.SUMMARIZING
        
        # Update status in AppSync
        appsync_service = None
        try:
            appsync_service = DocumentAppSyncService()
            logger.info(f"Updating document status to {document.status} in AppSync")
            appsync_service.update_document(document)
        except Exception as e:
            logger.warning(f"Failed to update document status in AppSync: {str(e)}")
            logger.warning("Continuing processing despite AppSync update failure")
        
        # Create the summarization service with provided config
        summarization_service = summarization.SummarizationService(
            config=CONFIG
        )        
        # Process the document using the service
        logger.info(f"Processing document with SummarizationService, document ID: {document.id}")
        processed_document = summarization_service.process_document(document)
        
        # Check if document processing failed
        if processed_document.status == Status.FAILED:
            error_message = f"Summarization failed for document {processed_document.id}"
            logger.error(error_message)
            # Update failure status in AppSync
            try:
                # Create a new service instance if we don't have one
                if not appsync_service:
                    appsync_service = DocumentAppSyncService()
                logger.info(f"Updating failure status in AppSync")
                appsync_service.update_document(processed_document)
            except Exception as e:
                logger.warning(f"Failed to update failure status in AppSync: {str(e)}")
            raise Exception(error_message)
        
        # Log the result
        if hasattr(processed_document, 'summary_report_uri') and processed_document.summary_report_uri:
            logger.info(f"Document summarization successful, report URI: {processed_document.summary_report_uri}")
        else:
            logger.warning("Document summarization completed but no summary report URI was set")
        
        # Return the processed document
        return {
            'document': processed_document.to_dict(),
        }
        
    except Exception as e:
        logger.error(f"Error in summarization function: {str(e)}", exc_info=True)
        raise e