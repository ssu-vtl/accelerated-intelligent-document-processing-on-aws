import boto3
import json
import os
from datetime import datetime, timezone

sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])
state_machine_arn = os.environ['STATE_MACHINE_ARN']

def handler(event, context):
    message = event['Records'][0]
    body = json.loads(message['body'])
    object_key = body['detail']['object']['key']
    
    execution = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(body)
    )
    
    tracking_table.update_item(
        Key={'object_key': object_key},
        UpdateExpression='SET #status = :status, execution_arn = :arn, start_time = :start',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'STARTED',
            ':arn': execution['executionArn'],
            ':start': datetime.now(timezone.utc).isoformat()
        }
    )
    
    return {'statusCode': 200, 'execution': execution['executionArn']}