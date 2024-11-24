import boto3
import time
from datetime import datetime, timedelta

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(event['table_name'])
    
    # Calculate TTL (90 days from now)
    ttl = int((datetime.now() + timedelta(days=90)).timestamp())
    
    # Write execution record
    table.put_item(Item={
        'object_key': event['detail']['object']['key'],
        'execution_arn': event['execution_arn'],
        'start_time': event['execution_start_time'],
        'ttl': ttl
    })
    
    return {
        'statusCode': 200,
        'execution_arn': event['execution_arn']
    }