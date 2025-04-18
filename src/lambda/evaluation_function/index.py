"""
Lambda function for evaluating document extraction results.

This module provides a lambda handler that evaluates document extraction results by comparing
them against baseline results using the EvaluationService from idp_common.
"""

import json
import os
import logging
import time
from typing import Dict, Any
from appsync_helper import AppSyncClient, UPDATE_DOCUMENT

# Import IDP common packages
from idp_common.models import Document
from idp_common import get_config, evaluation

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get bucket names from environment variables
METRIC_NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'GENAIDP')
BASELINE_BUCKET = os.environ['BASELINE_BUCKET']

print(os.environ["CONFIGURATION_TABLE_NAME"])

# Configuration
CONFIG = get_config()

# Create AppSync client
appsync = AppSyncClient()

def update_document_tracker(object_key: str, evaluationReportUri: str = None, evaluationStatus: str = None) -> Dict[str, Any]:
    """
    Update document status via AppSync
    
    Args:
        object_key: The document key
        evaluationReportUri: S3 path to generated evaluation report (optional)
        evaluationStatus: Status of the evaluation (optional)
        
    Returns:
        The updated document data
        
    Raises:
        AppSyncError: If the GraphQL operation fails
    """
    update_input = {
        'input': {
            'ObjectKey': object_key
        }
    }
    
    if evaluationReportUri is not None:
        update_input['input']['EvaluationReportUri'] = evaluationReportUri
        
    if evaluationStatus is not None:
        update_input['input']['EvaluationStatus'] = evaluationStatus
    
    logger.info(f"Updating document via AppSync: {update_input}")
    result = appsync.execute_mutation(UPDATE_DOCUMENT, update_input)
    return result['updateDocument']

def handler(event, context):
    """
    Lambda function handler
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Response with evaluation results
    """
    object_key = None
    try:
        logger.info(f"Starting evaluation process with event: {json.dumps(event, indent=2)}")
        start_time = time.time()
        
        # Extract data from event
        input_data = json.loads(event['detail']['input'])
        output_data = json.loads(event['detail']['output'])
        
        if output_data:
            # Get the processed document from the output data
            processed_result = output_data.get("ProcessedResult", {})
            if "document" in processed_result:
                # Get document from the final processing step
                actual_document = Document.from_dict(processed_result.get("document", {}))
                logger.info(f"Successfully loaded actual document with {len(actual_document.pages)} pages and {len(actual_document.sections)} sections")
                logger.info(f"Actual (Document): {actual_document}")
            else:
                logger.error("No document found in ProcessedResult")
                raise ValueError("No document found in ProcessedResult")
                
            # Extract the object key (input_key) for finding baseline documents
            object_key = actual_document.input_key
            
            # Update document status to STARTED
            update_document_tracker(object_key, evaluationStatus="STARTED")
            logger.info(f"Updated document evaluation status to STARTED")
            
            # Create expected document from baseline files in the baseline bucket
            logger.info(f"Loading baseline document for {object_key} from {BASELINE_BUCKET}")
            try:
                expected_document = Document.from_s3(
                    bucket=BASELINE_BUCKET, 
                    input_key=object_key
                )
                
                # Check if the expected document has any meaningful data
                if not expected_document.pages or not expected_document.sections:
                    logger.warning(f"No baseline data found for {object_key} in {BASELINE_BUCKET} (empty document)")
                    # Update document status to indicate no baseline data
                    update_document_tracker(object_key, evaluationStatus="NO_BASELINE")
                    logger.info(f"Updated document evaluation status to NO_BASELINE")
                    
                    # Exit without attempting evaluation
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'message': 'Evaluation skipped - no baseline data available',
                            'document_key': object_key
                        })
                    }
                
                # Baseline data exists and is valid
                logger.info(f"Successfully loaded expected (baseline) document with {len(expected_document.pages)} pages and {len(expected_document.sections)} sections")
                logger.info(f"Expected (Document): {expected_document}")
                
            except Exception as e:
                logger.error(f"Error loading baseline document: {str(e)}")
                # Update document status to FAILED before raising the exception
                if object_key:
                    update_document_tracker(object_key, evaluationStatus="FAILED")
                    logger.info(f"Updated document evaluation status to FAILED")
                raise ValueError(f"Failed to load baseline document: {str(e)}")
               
        # Create evaluation service
        evaluation_service = evaluation.EvaluationService(config=CONFIG)
        
        # Run evaluation
        logger.info(f"Starting evaluation for document {actual_document.id}")
        evaluated_document = evaluation_service.evaluate_document(
            actual_document=actual_document,
            expected_document=expected_document,
            store_results=True
        )
        
        # Get the evaluation report URI
        evaluation_report_uri = evaluated_document.evaluation_report_uri
        
        # Record execution time
        execution_time = time.time() - start_time
        
        # Update document status in AppSync to COMPLETED
        update_document_tracker(object_key, evaluation_report_uri, evaluationStatus="COMPLETED")
        logger.info(f"Document tracker updated with report URI and evaluation status COMPLETED")
                
        logger.info("Evaluation process completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Evaluation completed successfully',
                'report_location': evaluation_report_uri,
                'execution_time': execution_time
            })
        }
    
    except Exception as e:
        error_msg = f"Error in lambda_handler: {str(e)}"
        logger.error(error_msg)
        
        # Update document status to FAILED if we have the object key
        if object_key:
            try:
                update_document_tracker(object_key, evaluationStatus="FAILED")
                logger.info(f"Updated document evaluation status to FAILED")
            except Exception as update_error:
                logger.error(f"Failed to update evaluation status: {str(update_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Evaluation failed',
                'error': error_msg
            })
        }