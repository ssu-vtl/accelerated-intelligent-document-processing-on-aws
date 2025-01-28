import boto3
import os
import json
from datetime import datetime, timezone
import logging
from appsync_helper import AppSyncClient, CREATE_DOCUMENT, AppSyncError
import requests

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
sqs = boto3.client('sqs')
appsync = AppSyncClient()
queue_url = os.environ['QUEUE_URL']

def create_document(object_key: str, event_time: str) -> dict:
    """
    Create a document record via AppSync
    
    Args:
        object_key: The S3 object key
        event_time: The original event time
        
    Returns:
        The created document data
        
    Raises:
        AppSyncError: If the GraphQL operation fails
    """
    create_input = {
        'input': {
            'object_key': object_key,
            'status': 'QUEUED',
            'queued_time': datetime.now(timezone.utc).isoformat(),
            'initial_event_time': event_time
        }
    }
    
    logger.info(f"Creating document via AppSync: {create_input}")
    result = appsync.execute_mutation(CREATE_DOCUMENT, create_input)
    return result['createDocument']

def send_to_sqs(event: dict) -> dict:
    """
    Send message to SQS
    
    Args:
        event: The event to send
        
    Returns:
        SQS response
        
    Raises:
        botocore.exceptions.ClientError: If SQS operation fails
    """
    message = {
        'QueueUrl': queue_url,
        'MessageBody': json.dumps(event)
    }
    logger.info(f"Sending SQS message: {message}")
    return sqs.send_message(**message)

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    try:
        detail = event['detail']
        object_key = detail['object']['key']
        logger.info(f"Processing file: {object_key}")
        
        try:
            # First create document
            document = create_document(object_key, event['time'])
            logger.info(f"Document created: {document}")
            
            # Then send to SQS
            sqs_response = send_to_sqs(event)
            logger.info(f"Message sent to SQS: {sqs_response}")
            
            return {
                'statusCode': 200,
                'body': {
                    'detail': detail,
                    'document': document,
                    'sqs_message_id': sqs_response.get('MessageId')
                }
            }
            
        except AppSyncError as e:
            logger.error(f"Failed to create document in AppSync: {str(e)}")
            logger.error(f"GraphQL Errors: {e.errors}")
            raise  # Re-raise to trigger Lambda failure
            
        except requests.RequestException as e:
            logger.error(f"HTTP request to AppSync failed: {str(e)}")
            raise  # Re-raise to trigger Lambda failure
            
        except Exception as e:
            logger.error(f"Unexpected error processing {object_key}: {str(e)}", exc_info=True)
            raise  # Re-raise to trigger Lambda failure
            
    except KeyError as e:
        error_msg = f"Invalid event structure - missing key: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)  # Raise as ValueError to indicate invalid input
        
    except Exception as e:
        logger.error(f"Unexpected error in handler: {str(e)}", exc_info=True)
        raise  # Re-raise to trigger Lambda failure