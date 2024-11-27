import boto3
import json
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
concurrency_table = dynamodb.Table(os.environ['CONCURRENCY_TABLE'])
state_machine_arn = os.environ['STATE_MACHINE_ARN']
MAX_CONCURRENT = int(os.environ.get('MAX_CONCURRENT', '5'))
COUNTER_ID = 'workflow_counter'

def initialize_counter():
    try:
        concurrency_table.put_item(
            Item={
                'counter_id': COUNTER_ID,
                'active_count': 0
            },
            ConditionExpression='attribute_not_exists(counter_id)'
        )
        logger.info("Counter initialized")
    except ClientError as e:
        if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
            logger.error(f"Error initializing counter: {e}")
            raise
        logger.info("Counter already exists")

def update_counter(increment=True):
    logger.info(f"Updating counter: increment={increment}, max={MAX_CONCURRENT}")
    try:
        update_args = {
            'Key': {'counter_id': COUNTER_ID},
            'UpdateExpression': 'ADD active_count :inc',
            'ExpressionAttributeValues': {
                ':inc': 1 if increment else -1,
                ':max': MAX_CONCURRENT
            },
            'ReturnValues': 'UPDATED_NEW'
        }
        
        if increment:
            update_args['ConditionExpression'] = 'active_count < :max'
        
        logger.info(f"Counter update args: {update_args}")
        response = concurrency_table.update_item(**update_args)
        logger.info(f"Counter update response: {response}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning("Concurrency limit reached")
            return False
        logger.error(f"Error updating counter: {e}")
        raise

def handler(event, context):
    logger.info(f"Processing event: {json.dumps(event)}")
    
    # Initialize counter if needed
    initialize_counter()
    
    message = event['Records'][0]
    body = json.loads(message['body'])
    object_key = body['detail']['object']['key']
    logger.info(f"Processing file: {object_key}")
    
    # Try to increment counter
    if not update_counter(increment=True):
        logger.warning(f"Concurrency limit reached for {object_key}")
        raise Exception("Concurrency limit reached")
    
    try:
        # Start workflow
        logger.info(f"Starting workflow for {object_key}")
        execution = sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(body)
        )
        logger.info(f"Workflow started: {execution['executionArn']}")
        
        # Update tracking
        tracking_update = {
            'Key': {'object_key': object_key},
            'UpdateExpression': 'SET #status = :status, execution_arn = :arn, workflow_start_time = :start',
            'ExpressionAttributeNames': {'#status': 'status'},
            'ExpressionAttributeValues': {
                ':status': 'STARTED',
                ':arn': execution['executionArn'],
                ':start': datetime.now(timezone.utc).isoformat()
            }
        }
        logger.info(f"Updating tracking: {tracking_update}")
        tracking_table.update_item(**tracking_update)
        
        return {'statusCode': 200, 'execution': execution['executionArn']}
        
    except Exception as e:
        logger.error(f"Error processing {object_key}: {str(e)}", exc_info=True)
        # If anything fails, decrement the counter
        update_counter(increment=False)
        raise