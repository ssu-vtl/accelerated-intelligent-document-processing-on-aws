import boto3
import json
import os
from datetime import datetime, timezone
import logging
from appsync_helper import AppSyncClient, UPDATE_DOCUMENT, AppSyncError
import requests
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
appsync = AppSyncClient()
concurrency_table = dynamodb.Table(os.environ['CONCURRENCY_TABLE'])
COUNTER_ID = 'workflow_counter'

def put_latency_metrics(item: Dict[str, Any]) -> None:
    """
    Publish latency metrics to CloudWatch
    
    Args:
        item: Document data containing timestamps
        
    Raises:
        ValueError: If required timestamps are missing
        ClientError: If CloudWatch operation fails
    """
    try:
        # Validate required timestamps
        required_timestamps = ['initial_event_time', 'queued_time', 'workflow_start_time']
        missing = [ts for ts in required_timestamps if not item.get(ts)]
        if missing:
            raise ValueError(f"Missing required timestamps: {', '.join(missing)}")

        now = datetime.now(timezone.utc)
        initial_time = datetime.fromisoformat(item['initial_event_time'])
        queued_time = datetime.fromisoformat(item['queued_time'])
        workflow_start_time = datetime.fromisoformat(item['workflow_start_time'])
        
        queue_latency = (workflow_start_time - queued_time).total_seconds() * 1000
        workflow_latency = (now - workflow_start_time).total_seconds() * 1000
        total_latency = (now - initial_time).total_seconds() * 1000
        
        logger.info(
            f"Publishing latency metrics - queue: {queue_latency}ms, "
            f"workflow: {workflow_latency}ms, total: {total_latency}ms"
        )
        
        cloudwatch.put_metric_data(
            Namespace=f'{METRIC_NAMESPACE}',
            MetricData=[
                {
                    'MetricName': 'QueueLatencyMilliseconds',
                    'Value': queue_latency,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'WorkflowLatencyMilliseconds',
                    'Value': workflow_latency,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'TotalLatencyMilliseconds',
                    'Value': total_latency,
                    'Unit': 'Milliseconds'
                }
            ]
        )
    except ValueError as e:
        logger.error(f"Invalid timestamps in metrics data: {e}")
        raise
    except ClientError as e:
        logger.error(f"Failed to publish CloudWatch metrics: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error publishing metrics: {e}", exc_info=True)
        raise

def decrement_counter() -> Optional[int]:
    """
    Decrement the concurrency counter
    
    Returns:
        The new counter value or None if operation failed
        
    Note: This function handles its own errors
    """
    try:
        logger.info("Decrementing concurrency counter")
        response = concurrency_table.update_item(
            Key={'counter_id': COUNTER_ID},
            UpdateExpression='ADD active_count :dec',
            ExpressionAttributeValues={':dec': -1},
            ReturnValues='UPDATED_NEW'
        )
        new_count = response.get('Attributes', {}).get('active_count')
        logger.info(f"Counter decremented. New value: {new_count}")
        return new_count
    except ClientError as e:
        logger.error(f"Failed to decrement counter: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error decrementing counter: {e}", exc_info=True)
        return None

def update_document_completion(object_key: str, workflow_status: str) -> Dict[str, Any]:
    """
    Update document completion status via AppSync
    
    Args:
        object_key: The document key
        workflow_status: The final workflow status
        
    Returns:
        The updated document data
        
    Raises:
        AppSyncError: If the GraphQL operation fails
    """
    completion_time = datetime.now(timezone.utc).isoformat()
    
    update_input = {
        'input': {
            'object_key': object_key,
            'status': 'COMPLETED' if workflow_status == 'SUCCEEDED' else 'FAILED',
            'completion_time': completion_time,
            'workflow_status': workflow_status
        }
    }
    
    logger.info(f"Updating document via AppSync: {update_input}")
    result = appsync.execute_mutation(UPDATE_DOCUMENT, update_input)
    return result['updateDocument']

def extract_object_key(event: Dict[str, Any]) -> str:
    """
    Extract object key from Step Functions event
    
    Args:
        event: Step Functions state change event
        
    Returns:
        The object key
        
    Raises:
        ValueError: If event structure is invalid
        json.JSONDecodeError: If input JSON is invalid
    """
    try:
        input_data = json.loads(event['detail']['input'])
        object_key = input_data['detail']['object']['key']
        logger.info(f"Extracted object key from event: {object_key}")
        return object_key
    except KeyError as e:
        raise ValueError(f"Missing required field in event: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in event input: {e}")

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    counter_value = None
    
    try:
        # Extract data from event
        object_key = extract_object_key(event)
        workflow_status = event['detail']['status']
        
        try:
            # Update document completion status
            updated_doc = update_document_completion(object_key, workflow_status)
            
            # Publish metrics for successful executions
            if workflow_status == 'SUCCEEDED':
                try:
                    logger.info("Workflow succeeded, publishing latency metrics")
                    put_latency_metrics(updated_doc)
                except Exception as metrics_error:
                    logger.error(f"Failed to publish metrics: {metrics_error}", exc_info=True)
                    # Continue processing even if metrics fail
            else:
                logger.info(
                    f"Workflow did not succeed (status: {workflow_status}), "
                    "skipping latency metrics"
                )
            
            # Always try to decrement counter
            counter_value = decrement_counter()
            
            return {
                'statusCode': 200,
                'body': {
                    'object_key': object_key,
                    'workflow_status': workflow_status,
                    'completion_time': updated_doc['completion_time'],
                    'counter_value': counter_value
                }
            }
            
        except AppSyncError as e:
            logger.error(f"Failed to update document in AppSync: {str(e)}")
            logger.error(f"GraphQL Errors: {e.errors}")
            decrement_counter()  # Still try to decrement counter
            raise
            
        except requests.RequestException as e:
            logger.error(f"HTTP request to AppSync failed: {str(e)}")
            decrement_counter()  # Still try to decrement counter
            raise
            
    except ValueError as e:
        logger.error(f"Invalid event data: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in handler: {str(e)}", exc_info=True)
        # Always try to decrement counter in case of any error
        if counter_value is None:
            decrement_counter()
        raise