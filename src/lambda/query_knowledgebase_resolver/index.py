# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import boto3
import re
import urllib.parse
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")))
# Get LOG_LEVEL from environment variable with INFO as default

print("Boto3 version: ", boto3.__version__)

# Knowledge Base Type Configuration
KB_TYPE = os.environ.get("KB_TYPE", "BEDROCK")  # "BEDROCK" or "S3_VECTORS"
logger.info(f"Query Knowledge Base Resolver initialized with KB_TYPE: {KB_TYPE}")

# Bedrock KB Configuration
KB_ID = os.environ.get("KB_ID")
KB_ACCOUNT_ID = os.environ.get("KB_ACCOUNT_ID")
KB_REGION = os.environ.get("KB_REGION") or os.environ["AWS_REGION"]
MODEL_ID = os.environ.get("MODEL_ID")
MODEL_ARN = f"arn:aws:bedrock:{KB_REGION}:{KB_ACCOUNT_ID}:inference-profile/{MODEL_ID}"
GUARDRAIL_ENV = os.environ.get("GUARDRAIL_ID_AND_VERSION", "")

# S3 Vectors Configuration
S3_VECTORS_QUERY_FUNCTION_NAME = os.environ.get("S3_VECTORS_QUERY_FUNCTION_NAME", "")

# Initialize clients
KB_CLIENT = boto3.client(
    service_name="bedrock-agent-runtime",
    region_name=KB_REGION
)

LAMBDA_CLIENT = boto3.client("lambda", region_name=KB_REGION)

# Validate configuration based on KB_TYPE
if KB_TYPE == "S3_VECTORS":
    if not S3_VECTORS_QUERY_FUNCTION_NAME:
        logger.error("S3_VECTORS_QUERY_FUNCTION_NAME must be configured when KB_TYPE=S3_VECTORS")
    else:
        logger.info(f"S3 Vectors backend configured with query function: {S3_VECTORS_QUERY_FUNCTION_NAME}")
elif KB_TYPE == "BEDROCK":
    if not KB_ID:
        logger.error("KB_ID must be configured when KB_TYPE=BEDROCK")
    else:
        logger.info(f"Bedrock KB backend configured with KB_ID: {KB_ID}")
else:
    logger.error(f"Invalid KB_TYPE: {KB_TYPE}. Must be 'BEDROCK' or 'S3_VECTORS'")

def get_kb_response(query, sessionId):
    input = {
        "input": {
            'text': query
        },
        "retrieveAndGenerateConfiguration": {
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KB_ID,
                'modelArn': MODEL_ARN,
            },
            'type': 'KNOWLEDGE_BASE'
        }
    }
    
    # Apply Bedrock Guardrail if configured
    if GUARDRAIL_ENV:
        try:
            guardrail_id, guardrail_version = GUARDRAIL_ENV.split(":")
            if guardrail_id and guardrail_version:
                if "generationConfiguration" not in input["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"]:
                    input["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"]["generationConfiguration"] = {}
                
                input["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"]["generationConfiguration"]["guardrailConfiguration"] = {
                    "guardrailId": guardrail_id,
                    "guardrailVersion": guardrail_version
                }
                logger.debug(f"Using Bedrock Guardrail ID: {guardrail_id}, Version: {guardrail_version}")
        except ValueError:
            logger.warning(f"Invalid GUARDRAIL_ID_AND_VERSION format: {GUARDRAIL_ENV}. Expected format: 'id:version'")
    
    if sessionId:
        input["sessionId"] = sessionId
    
    logger.info("Amazon Bedrock KB Request: %s", json.dumps(input))
    try:
        resp = KB_CLIENT.retrieve_and_generate(**input)
    except Exception as e:
        logger.error("Amazon Bedrock KB Exception: %s", e)
        resp = {
            "systemMessage": "Amazon Bedrock KB Error: " + str(e)
        }
    logger.debug("Amazon Bedrock KB Response: %s", json.dumps(resp))
    return resp

def extract_document_id(s3_uri, reference_metadata=None):
    """Extract document ID from S3 URI, handling both Bedrock KB and S3 Vectors formats."""
    
    # For S3 Vectors, prefer document_id from metadata if available
    if reference_metadata and 'document_id' in reference_metadata:
        return reference_metadata['document_id']
    
    # Fallback to extracting from S3 URI (Bedrock KB format)
    # Strip out the s3://bucketname/ prefix
    without_bucket = re.sub(r'^s3://[^/]+/', '', s3_uri)
    # Remove everything from /sections or /pages to the end
    document_id = re.sub(r'/(sections|pages)/.*$', '', without_bucket)
    return document_id


def markdown_response(kb_response):
    """Generate markdown response for UI compatibility."""

    import urllib.parse  # Add this import for URL encoding
    
    showContextText = True
    message = kb_response.get("output", {}).get("text", {}) or kb_response.get(
        "systemMessage") or "No answer found"
    markdown = message
    if showContextText:
        contextText = ""
        sourceLinks = []
        for source in kb_response.get("citations", []):
            for reference in source.get("retrievedReferences", []):
                snippet = reference.get("content", {}).get(
                    "text", "no reference text")
                
                # Truncate long snippets for readability
                if len(snippet) > 300:
                    snippet = snippet[:300] + "..."
                
                if 'location' in reference and 's3Location' in reference['location']:
                    s3_uri = reference['location']['s3Location']['uri']
                    
                    # Get metadata for S3 Vectors compatibility
                    reference_metadata = reference.get('metadata', {})
                    
                    # Extract document ID using the enhanced function
                    documentId = extract_document_id(s3_uri, reference_metadata)
                    
                    # URL encode the documentId to make it URL-safe
                    url_safe_documentId = urllib.parse.quote(documentId, safe='')
                    url = f"{url_safe_documentId}"
                    title = documentId
                    contextText = f'{contextText}<br><documentId href="{url}">{title}</documentId><br>{snippet}\n'
                    sourceLinks.append(f'<documentId href="{url}">{title}</documentId>')
        if contextText:
            markdown = f'{markdown}\n<details><summary>Context</summary><p style="white-space: pre-line;">{contextText}</p></details>'
        if len(sourceLinks):
            # Remove duplicate sources before joining
            unique_sourceLinks = list(dict.fromkeys(sourceLinks))
            markdown = f'{markdown}<br>Sources: ' + ", ".join(unique_sourceLinks)
    return markdown


def get_s3_vectors_response(query, session_id):
    """Route query to S3 Vector Query Lambda function."""

    try:
        if not S3_VECTORS_QUERY_FUNCTION_NAME:
            raise Exception("S3_VECTORS_QUERY_FUNCTION_NAME environment variable not configured")
        
        # Prepare event payload for S3 Vector Query Lambda
        # This matches the GraphQL event structure expected by the S3 vector query function
        s3_vector_event = {
            "arguments": {
                "input": query
            }
        }
        
        # Add session ID if provided
        if session_id:
            s3_vector_event["arguments"]["sessionId"] = session_id
        
        logger.info(f"Invoking S3 Vector Query Lambda: {S3_VECTORS_QUERY_FUNCTION_NAME}")
        logger.debug(f"S3 Vector Query event: {json.dumps(s3_vector_event)}")
        
        # Invoke S3 Vector Query Lambda function
        response = LAMBDA_CLIENT.invoke(
            FunctionName=S3_VECTORS_QUERY_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(s3_vector_event)
        )
        
        # Parse Lambda response
        payload = response['Payload'].read()
        
        if response.get('StatusCode') != 200:
            raise Exception(f"S3 Vector Query Lambda failed with status: {response.get('StatusCode')}")
        
        # The S3 Vector Query Lambda returns a JSON string, so we need to parse it
        s3_vector_response = json.loads(payload.decode('utf-8'))
        
        logger.debug(f"S3 Vector Query response: {json.dumps(s3_vector_response)}")
        
        # Verify response format matches Bedrock KB structure
        if not isinstance(s3_vector_response, dict):
            raise Exception("Invalid response format from S3 Vector Query Lambda")
        
        return s3_vector_response
        
    except Exception as e:
        logger.error(f"Error in S3 Vectors backend: {str(e)}")
        
        # Return error response in Bedrock KB format for consistency
        return {
            "systemMessage": f"S3 Vectors Backend Error: {str(e)}",
            "output": {"text": "I apologize, but I encountered an error while searching the knowledge base. Please try again."},
            "citations": []
        }


def handler(event, context):
    print("Received event: %s" % json.dumps(event))
    query = event["arguments"]["input"]
    sessionId = event["arguments"].get("sessionId") or None
    
    # Route to appropriate backend based on KB_TYPE
    if KB_TYPE == "S3_VECTORS":
        logger.info("Routing query to S3 Vectors backend")
        kb_response = get_s3_vectors_response(query, sessionId)
    else:
        logger.info("Routing query to Bedrock KB backend")
        kb_response = get_kb_response(query, sessionId)
    
    # Add markdown formatting for UI compatibility (identical for both backends)
    kb_response["markdown"] = markdown_response(kb_response)
    
    print("Returning response: %s" % json.dumps(kb_response))
    return json.dumps(kb_response)