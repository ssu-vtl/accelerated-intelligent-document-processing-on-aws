import boto3
import json
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def calculate_durations(timestamps):
    try:
        durations = {}
        if 'queued_time' in timestamps and 'workflow_start_time' in timestamps:
            queue_time = (datetime.fromisoformat(timestamps['workflow_start_time']) - 
                         datetime.fromisoformat(timestamps['queued_time'])).total_seconds() * 1000
            durations['queue'] = int(queue_time)
            
        if 'workflow_start_time' in timestamps and 'completion_time' in timestamps:
            processing_time = (datetime.fromisoformat(timestamps['completion_time']) - 
                             datetime.fromisoformat(timestamps['workflow_start_time'])).total_seconds() * 1000
            durations['processing'] = int(processing_time)
            
        if 'initial_event_time' in timestamps and 'completion_time' in timestamps:
            total_time = (datetime.fromisoformat(timestamps['completion_time']) - 
                         datetime.fromisoformat(timestamps['initial_event_time'])).total_seconds() * 1000
            durations['total'] = int(total_time)
            
        return durations
    except Exception as e:
        logger.error(f"Error calculating durations: {e}", exc_info=True)
        return {}

def handler(event, context):

    logger.info(f"Event: {json.dumps(event)}")

    s3_key = event.get('s3_key')
    if not s3_key:
        return {'status': 'ERROR', 'message': 's3_key is required'}
    
    dynamodb = boto3.resource('dynamodb')
    tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
    sfn = boto3.client('stepfunctions')
    
    try:
        response = tracking_table.get_item(
            Key={'object_key': s3_key},
            ConsistentRead=True
        )
        
        if 'Item' not in response:
            return {'status': 'NOT_FOUND'}
            
        item = response['Item']
        timestamps = {
            'initial_event_time': item.get('initial_event_time'),
            'queued_time': item.get('queued_time'),
            'workflow_start_time': item.get('workflow_start_time'),
            'completion_time': item.get('completion_time')
        }
        
        result = {
            'status': item.get('status'),
            'timing': {
                'timestamps': timestamps,
                'elapsed': calculate_durations(timestamps)
            }
        }
        
        execution_arn = item.get('execution_arn')
        if execution_arn:
            try:
                execution = sfn.describe_execution(executionArn=execution_arn)
                history = sfn.get_execution_history(
                    executionArn=execution_arn,
                    maxResults=100
                )
                
                result['processingDetail'] = {
                    'executionArn': execution_arn,
                    'execution': {k: str(v) if isinstance(v, datetime) else v 
                                for k, v in execution.items() 
                                if k != 'ResponseMetadata'},
                    'events': [{k: str(v) if isinstance(v, datetime) else v 
                              for k, v in event.items()}
                              for event in history['events']]
                }
            except Exception as e:
                logger.error(f"Error getting Step Functions details: {e}", exc_info=True)
                result['processingDetail'] = {
                    'executionArn': execution_arn,
                    'error': str(e)
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Error looking up document: {e}", exc_info=True)
        return {
            'status': 'ERROR',
            'message': str(e)
        }
