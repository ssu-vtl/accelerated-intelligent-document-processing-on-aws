import boto3
import json
import os

def handler(event, context):
    s3_key = event.get('s3_key')
    if not s3_key:
        raise ValueError("s3_key is required")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TRACKING_TABLE'])
    
    response = table.get_item(Key={'object_key': s3_key})
    
    if 'Item' not in response:
        return {
            'found': False,
            'message': f'No record found for S3 key: {s3_key}'
        }
        
    item = response['Item']
    
    if item['status'] == 'QUEUED':
        return {
            'found': True,
            'status': 'QUEUED',
            'queued_time': item['queued_time']
        }
        
    # Get execution details if started
    if 'execution_arn' in item:
        sfn = boto3.client('stepfunctions')
        execution = sfn.describe_execution(executionArn=item['execution_arn'])
        history = sfn.get_execution_history(
            executionArn=item['execution_arn'],
            maxResults=100
        )
        
        return {
            'found': True,
            'status': item['status'],
            'queued_time': item['queued_time'],
            'execution': {
                'arn': item['execution_arn'],
                'status': execution['status'],
                'startDate': execution['startDate'].isoformat(),
                'stopDate': execution.get('stopDate', '').isoformat() if 'stopDate' in execution else None,
                'input': json.loads(execution['input']),
                'output': json.loads(execution['output']) if 'output' in execution else None
            },
            'events': [{
                'type': event['type'],
                'timestamp': event['timestamp'].isoformat(),
                'details': {k: v for k, v in event.items() if k not in ['type', 'timestamp']}
            } for event in history['events']]
        }