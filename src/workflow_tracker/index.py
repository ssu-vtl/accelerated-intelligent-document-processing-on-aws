import boto3
import json
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
concurrency_table = dynamodb.Table(os.environ['CONCURRENCY_TABLE'])
COUNTER_ID = 'workflow_counter'

def put_latency_metrics(item, completion_time):
    try:
        initial_time = datetime.fromisoformat(item['initial_event_time'])
        queued_time = datetime.fromisoformat(item['queued_time'])
        workflow_start_time = datetime.fromisoformat(item['workflow_start_time'])
        workflow_end_time = datetime.fromisoformat(completion_time)
        
        queue_latency = (workflow_start_time - queued_time).total_seconds() * 1000
        workflow_latency = (workflow_end_time - workflow_start_time).total_seconds() * 1000
        total_latency = (workflow_end_time - initial_time).total_seconds() * 1000
        
        logger.info(f"Publishing latency metrics - queue: {queue_latency}ms, workflow: {workflow_latency}ms, total: {total_latency}ms")
        
        cloudwatch.put_metric_data(
            Namespace='DocumentProcessing',
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
    
    execution_arn = event['detail']['executionArn']
    workflow_status = event['detail']['status']
    completion_time = datetime.now(timezone.utc).isoformat()
    
    try:
        # Find tracking record by execution ARN
        response = tracking_table.scan(
            FilterExpression='execution_arn = :arn',
            ExpressionAttributeValues={':arn': execution_arn}
        )
        
        if not response.get('Items'):
            logger.error(f"No tracking record found for execution {execution_arn}")
            return
            
        item = response['Items'][0]
        object_key = item['object_key']
        
        # Update tracking record
        tracking_table.update_item(
            Key={'object_key': object_key},
            UpdateExpression='SET #status = :status, completion_time = :completion, workflow_status = :workflow_status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED' if workflow_status == 'SUCCEEDED' else 'FAILED',
                ':completion': completion_time,
                ':workflow_status': workflow_status
            }
        )
        
        # Publish metrics
        if workflow_status == 'SUCCEEDED':
            put_latency_metrics(item, completion_time)
        
        # Decrement concurrency counter
        concurrency_table.update_item(
            Key={'counter_id': COUNTER_ID},
            UpdateExpression='ADD active_count :dec',
            ExpressionAttributeValues={':dec': -1}
        )
        
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
            concurrency_table.update_item(
                Key={'counter_id': COUNTER_ID},
                UpdateExpression='ADD active_count :dec',
                ExpressionAttributeValues={':dec': -1}
            )
        except Exception as counter_error:
            logger.error(f"Failed to decrement counter: {counter_error}")
        raise