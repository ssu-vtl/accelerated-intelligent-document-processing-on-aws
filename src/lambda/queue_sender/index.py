# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.

import boto3
import os
import json
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
queue_url = os.environ['QUEUE_URL']

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    detail = event['detail']
    object_key = detail['object']['key']
    logger.info(f"Processing file: {object_key}")
    
    # Record in DynamoDB
    tracking_item = {
        'object_key': object_key,
        'status': 'QUEUED',
        'queued_time': datetime.now(timezone.utc).isoformat(),
        'initial_event_time': event['time']  # Original S3 event time
    }
    logger.info(f"Recording tracking entry: {tracking_item}")
    tracking_table.put_item(Item=tracking_item)
    
    # Send to SQS queue
    message = {
        'QueueUrl': queue_url,
        'MessageBody': json.dumps(event)
    }
    logger.info(f"Sending SQS message: {message}")
    response = sqs.send_message(**message)
    logger.info(f"SQS response: {response}")
    
    return {'statusCode': 200, 'detail': detail}