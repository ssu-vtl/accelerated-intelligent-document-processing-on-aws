import boto3
import json

def handler(event, context):
    s3_client = boto3.client('s3')
    textract_client = boto3.client('textract')
    
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    
    response = textract_client.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    
    return {
        'text': ' '.join([block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE'])
    }