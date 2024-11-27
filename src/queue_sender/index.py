import boto3
import os
import json
from datetime import datetime, timezone

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
queue_url = os.environ['QUEUE_URL']

def handler(event, context):
    detail = event['detail']
    object_key = detail['object']['key']
    
    tracking_table.put_item(Item={
        'object_key': object_key,
        'status': 'QUEUED',
        'queued_time': datetime.now(timezone.utc).isoformat()
    })
    
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event),
        MessageGroupId='documents',
        MessageDeduplicationId=object_key
    )
    
    return {'statusCode': 200, 'detail': detail}