# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import boto3
import json
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

METRIC_NAMESPACE = os.environ['METRIC_NAMESPACE']

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
concurrency_table = dynamodb.Table(os.environ['CONCURRENCY_TABLE'])
COUNTER_ID = 'workflow_counter'

def put_latency_metrics(item):
    try:
        now = datetime.now(timezone.utc)
        initial_time = datetime.fromisoformat(item['initial_event_time'])
        queued_time = datetime.fromisoformat(item['queued_time'])
        workflow_start_time = datetime.fromisoformat(item['workflow_start_time'])
        
        queue_latency = (workflow_start_time - queued_time).total_seconds() * 1000
        workflow_latency = (now - workflow_start_time).total_seconds() * 1000
        total_latency = (now - initial_time).total_seconds() * 1000
        
        logger.info(f"Publishing latency metrics - queue: {queue_latency}ms, workflow: {workflow_latency}ms, total: {total_latency}ms")
        
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
    except Exception as e:
        logger.error(f"Error publishing latency metrics: {e}", exc_info=True)

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    # Get the original input from the execution
    try:
        input_data = json.loads(event['detail']['input'])
        object_key = input_data['detail']['object']['key']
        logger.info(f"Extracted object key from event: {object_key}")
    except Exception as e:
        logger.error(f"Error extracting object key from event: {e}")
        raise

    try:
        completion_time = datetime.now(timezone.utc).isoformat()
        workflow_status = event['detail']['status']
        
        # Get current tracking record using consistent read
        logger.info(f"Performing consistent read for tracking record: {object_key}")
        response = tracking_table.get_item(
            Key={'object_key': object_key},
            ConsistentRead=True
        )
        
        if 'Item' not in response:
            error_msg = f"No tracking record found for {object_key} (with consistent read)"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        item = response['Item']
        logger.info(f"Retrieved tracking record: {json.dumps(item)}")
        
        # Update tracking record
        update_expression = 'SET #status = :status, completion_time = :completion, workflow_status = :workflow_status'
        update_values = {
            ':status': 'COMPLETED' if workflow_status == 'SUCCEEDED' else 'FAILED',
            ':completion': completion_time,
            ':workflow_status': workflow_status
        }
        
        logger.info(f"Updating tracking record with values: {json.dumps(update_values)}")
        tracking_table.update_item(
            Key={'object_key': object_key},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=update_values
        )
        
        # Publish metrics for successful executions
        if workflow_status == 'SUCCEEDED':
            logger.info("Workflow succeeded, publishing latency metrics")
            put_latency_metrics(item)
        else:
            logger.info(f"Workflow did not succeed (status: {workflow_status}), skipping latency metrics")
        
        # Decrement concurrency counter
        logger.info("Decrementing concurrency counter")
        counter_response = concurrency_table.update_item(
            Key={'counter_id': COUNTER_ID},
            UpdateExpression='ADD active_count :dec',
            ExpressionAttributeValues={':dec': -1},
            ReturnValues='UPDATED_NEW'
        )
        logger.info(f"Counter decremented. New value: {counter_response.get('Attributes', {}).get('active_count')}")
        
        logger.info(f"Workflow tracking updated for {object_key}: {workflow_status}")
        
        return {
            'statusCode': 200,
            'object_key': object_key,
            'workflow_status': workflow_status,
            'completion_time': completion_time
        }
        
    except Exception as e:
        logger.error(f"Error processing workflow completion: {e}", exc_info=True)
        # Still try to decrement counter even if other operations fail
        try:
            logger.info("Attempting to decrement counter after error")
            concurrency_table.update_item(
                Key={'counter_id': COUNTER_ID},
                UpdateExpression='ADD active_count :dec',
                ExpressionAttributeValues={':dec': -1}
            )
            logger.info("Successfully decremented counter after error")
        except Exception as counter_error:
            logger.error(f"Failed to decrement counter: {counter_error}", exc_info=True)
        raise