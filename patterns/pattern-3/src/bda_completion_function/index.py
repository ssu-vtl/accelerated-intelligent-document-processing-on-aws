# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.
import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])

def get_task_token(object_key: str) -> str:
    try:
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
        return item['task_token']

    except Exception as e:
        logger.error(f"Error retrieving tracking record: {e}")
        raise

def send_task_response(task_token: str, job_status: str, error_message: str = None):
    try:
        if job_status == 'SUCCESS':
            logger.info(f"Sending task success for token: {task_token}")
            stepfunctions.send_task_success(
                taskToken=task_token,
                output=json.dumps({
                    'status': 'SUCCESS'
                })
            )
        else:
            logger.info(f"Sending task failure for token: {task_token}")
            stepfunctions.send_task_failure(
                taskToken=task_token,
                error='JobExecutionError',
                cause=error_message or 'Job execution failed'
            )
    except Exception as e:
        logger.error(f"Error sending task response: {e}")
        raise

def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Extract required information from event
        object_key = event['detail']['input_s3_object']['name']
        job_status = event['detail']['job_status']
        error_message = event['detail'].get('error_message')
        
        logger.info(f"Processing job completion for object: {object_key}, status: {job_status}")
        
        # Get the task token from DynamoDB
        task_token = get_task_token(object_key)
        logger.info(f"Retrieved task_token: {task_token}")
        
        # Send appropriate response to Step Functions
        send_task_response(task_token, job_status, error_message)
        
        return {
            'statusCode': 200,
            'body': 'Task response sent successfully'
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise