# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import logging
import os
from typing import Dict, Any

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Import the common assessment service
try:
    from idp_common.assessment.service import AssessmentService
    from idp_common.models import Document
    from idp_common import s3
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for document assessment.
    
    This function assesses the confidence of extraction results for a document section
    using the Assessment service from the idp_common library.
    
    Args:
        event: Lambda event containing document and section information
        context: Lambda context object
        
    Returns:
        Updated document with assessment results
    """
    logger.info(f"Starting assessment processing for event: {json.dumps(event, default=str)}")
    
    try:
        # Extract input from event
        document_dict = event.get('document', {})
        section_id = event.get('section_id')
        config = event.get('config', {})
        
        # Validate inputs
        if not document_dict:
            raise ValueError("No document provided in event")
            
        if not section_id:
            raise ValueError("No section_id provided in event")
            
        # Convert document dictionary to Document object
        document = Document.from_dict(document_dict)
        logger.info(f"Processing assessment for document {document.id}, section {section_id}")
        
        # Get configuration from DynamoDB if not provided in event
        if not config:
            config_table_name = os.environ.get('CONFIGURATION_TABLE_NAME')
            if config_table_name:
                try:
                    from idp_common.config.service import ConfigurationService
                    config_service = ConfigurationService(config_table_name)
                    config = config_service.get_configuration()
                    logger.info("Retrieved configuration from DynamoDB")
                except Exception as e:
                    logger.warning(f"Failed to retrieve configuration from DynamoDB: {e}")
                    config = {}
        
        # Initialize assessment service
        assessment_service = AssessmentService(
            region=os.environ.get('AWS_REGION'),
            config=config
        )
        
        # Process the document section for assessment
        logger.info(f"Starting assessment for section {section_id}")
        updated_document = assessment_service.process_document_section(document, section_id)
        
        # Check for errors
        if updated_document.errors:
            logger.warning(f"Assessment completed with {len(updated_document.errors)} errors")
            for error in updated_document.errors:
                logger.warning(f"Assessment error: {error}")
        else:
            logger.info(f"Assessment completed successfully for section {section_id}")
        
        # Return the updated document as a dictionary
        result = {
            'document': updated_document.to_dict(),
            'section_id': section_id
        }
        
        logger.info("Assessment processing completed")
        return result
        
    except Exception as e:
        error_msg = f"Error during assessment processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Return the original document with error added
        try:
            document = Document.from_dict(event.get('document', {}))
            document.errors.append(error_msg)
            return {
                'document': document.to_dict(),
                'section_id': event.get('section_id'),
                'error': error_msg
            }
        except Exception as fallback_error:
            logger.error(f"Failed to create error response: {fallback_error}")
            # Last resort fallback
            return {
                'document': event.get('document', {}),
                'section_id': event.get('section_id'),
                'error': error_msg
            }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda entry point.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Assessment result
    """
    return handler(event, context)
