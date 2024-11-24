import boto3
import json
import os

def handler(event, context):
    s3_key = event.get('s3_key')
    if not s3_key:
        raise ValueError("s3_key is required")
    
    # Get table name from environment
    table_name = os.environ['TABLE_NAME']
    
    # Look up execution in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'object_key': s3_key
        }
    )
    
    if 'Item' not in response:
        return {
            'found': False,
            'message': f'No execution found for S3 key: {s3_key}'
        }
    
    execution_arn = response['Item']['execution_arn']
    
    # Get execution details from Step Functions
    sfn = boto3.client('stepfunctions')
    
    execution = sfn.describe_execution(
        executionArn=execution_arn
    )
    
    history = sfn.get_execution_history(
        executionArn=execution_arn,
        maxResults=100
    )
    
    return {
        'found': True,
        'execution': {
            'arn': execution_arn,
            'status': execution['status'],
            'startDate': execution['startDate'].isoformat(),
            'stopDate': execution.get('stopDate', '').isoformat() if 'stopDate' in execution else None,
            'input': json.loads(execution['input']),
            'output': json.loads(execution['output']) if 'output' in execution else None,
        },
        'events': [{
            'type': event['type'],
            'timestamp': event['timestamp'].isoformat(),
            'details': {k: v for k, v in event.items() if k not in ['type', 'timestamp']}
        } for event in history['events']]
    }