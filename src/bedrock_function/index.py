import boto3
import json

def handler(event, context):
    bedrock = boto3.client('bedrock-runtime')
    s3_client = boto3.client('s3')
    
    text = event['text']
    
    prompt = f"""

    Human: Extract key information from this document text:
    {text}
    
    Format the response as JSON with relevant key-value pairs.

    Assistant: Here is the extracted information in JSON format:"""
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-v2',
        body=json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
            "temperature": 0,
            "anthropic_version": "bedrock-2023-05-31"
        })
    )
    
    result = json.loads(response['body'].read())
    
    s3_client.put_object(
        Bucket=event['outputBucket'],
        Key=f"processed/{event['detail']['object']['key']}.json",
        Body=json.dumps(result['completion'], indent=2)
    )
    
    return result
