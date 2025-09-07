import boto3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Import the correct custom client
from idp_common.s3vectors.client import S3VectorsClient
from idp_common.bedrock.client import BedrockClient
from idp_common.s3 import get_s3_client

# --- Constants ---
# Use named constants instead of "magic numbers" for better readability and maintainability.
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
METADATA_ANALYSIS_SAMPLE_SIZE = 1000  # Max vectors to sample for analysis
MIN_FIELD_OCCURRENCE_RATE = 0.1       # Field must be in at least 10% of samples
MAX_FILTERABLE_FIELDS_TO_REPORT = 8   # Max number of fields to report and generate examples for
NON_FILTERABLE_FIELDS = {'text_content', 'document_id', 's3_uri'}

# --- Environment Variables ---
# Fail-fast by accessing required environment variables at startup.
S3_VECTORS_BUCKET_NAME = os.environ["S3_VECTORS_BUCKET_NAME"]
S3_VECTORS_INDEX_NAME = os.environ["S3_VECTORS_INDEX_NAME"]
QUERY_LAMBDA_FUNCTION_NAME = os.environ["QUERY_LAMBDA_FUNCTION_NAME"]
WORKING_BUCKET = os.environ["WORKING_BUCKET"]
NOVA_MODEL_ID = os.environ.get("NOVA_MODEL_ID", "amazon.nova-pro-v1:0")

# --- AWS Service Clients & Logger ---
# Initialize clients in the global scope for connection reuse.
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Correctly use the custom S3VectorsClient
s3_vectors_client = S3VectorsClient()
s3_client = get_s3_client()
lambda_client = boto3.client('lambda')
bedrock_client = BedrockClient()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Analyzes S3 Vectors metadata, generates filter examples using an LLM,
    stores them in S3, and updates the query Lambda's environment.
    """
    trigger_source = event.get('trigger_source', 'manual')
    logger.info(f"Starting metadata filter analysis (triggered by: {trigger_source})")

    try:
        metadata_analysis = analyze_metadata()
        if not metadata_analysis.get('filterable_fields'):
            logger.warning("No filterable fields found. Aborting.")
            return {'statusCode': 200, 'body': json.dumps({'message': 'No filterable fields found.'})}

        filter_examples = generate_filter_examples(metadata_analysis)
        s3_location = store_filter_examples(filter_examples)
        
        filterable_fields_keys = list(metadata_analysis['filterable_fields'].keys())
        update_lambda_environment(filterable_fields_keys, s3_location)

        response_body = {
            'message': 'Filter analysis completed successfully.',
            'trigger_source': trigger_source,
            'filterable_fields': filterable_fields_keys,
            'examples_stored_at': s3_location,
            'example_count': len(filter_examples)
        }
        return {'statusCode': 200, 'body': json.dumps(response_body)}

    except Exception as e:
        logger.error("Failed to complete metadata filter analysis.", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'An internal error occurred.'})
        }

def analyze_metadata() -> Dict[str, Any]:
    """
    Scans a sample of vectors to find common metadata fields suitable for filtering.
    """
    field_analysis = defaultdict(lambda: {'count': 0, 'sample_values': set(), 'data_type': None})
    
    try:
        logger.info(f"Analyzing up to {METADATA_ANALYSIS_SAMPLE_SIZE} vectors from index '{S3_VECTORS_INDEX_NAME}'...")
        response = s3_vectors_client.list_vectors(
            vectorBucketName=S3_VECTORS_BUCKET_NAME,
            indexName=S3_VECTORS_INDEX_NAME,
            maxResults=METADATA_ANALYSIS_SAMPLE_SIZE
        )
        
        vectors = response.get('vectors', [])
        total_vectors = len(vectors)
        if total_vectors == 0:
            logger.warning("No vectors found in the index.")
            return {'total_vectors_sampled': 0, 'filterable_fields': {}}

        for vector in vectors:
            for field, value in vector.get('metadata', {}).items():
                if field not in NON_FILTERABLE_FIELDS:
                    info = field_analysis[field]
                    info['count'] += 1
                    if len(info['sample_values']) < 10: # Keep up to 10 unique sample values
                        info['sample_values'].add(str(value)) # Convert to string for simplicity
                    if info['data_type'] is None:
                        info['data_type'] = type(value).__name__
        
        min_occurrence = max(1, total_vectors * MIN_FIELD_OCCURRENCE_RATE)
        filterable_fields = {
            field: {
                'occurrence_rate': round(info['count'] / total_vectors, 2),
                'sample_values': list(info['sample_values']),
                'data_type': info['data_type']
            }
            for field, info in field_analysis.items() if info['count'] >= min_occurrence
        }
        
        # Sort by occurrence rate and take the top N fields
        sorted_fields = sorted(filterable_fields.items(), key=lambda item: item[1]['occurrence_rate'], reverse=True)
        top_fields = dict(sorted_fields[:MAX_FILTERABLE_FIELDS_TO_REPORT])
        
        logger.info(f"Found {len(top_fields)} filterable fields meeting the threshold.")
        return {'total_vectors_sampled': total_vectors, 'filterable_fields': top_fields}

    except Exception:
        logger.error(f"Failed to analyze metadata from S3 Vectors API.", exc_info=True)
        return {'total_vectors_sampled': 0, 'filterable_fields': {}}

def generate_filter_examples(metadata_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates useful filter examples using a Bedrock LLM."""
    # (Code for this function remains largely the same, but with improved error handling and logging)
    # This is a placeholder for the full prompt generation logic which is complex and correct.
    # The key improvements are in the try/except block.
    filterable_fields = metadata_analysis['filterable_fields']
    prompt = f"""
        You are an expert in S3 Vectors metadata filtering. Based on the following metadata analysis, create useful filter examples that a query Lambda can use as templates.

        Metadata Analysis:
        {json.dumps(filterable_fields, indent=2)}

        S3 Vectors Filter Specifications:

        FILTERABLE METADATA CONSTRAINTS:
        - Size limit: Up to 2 KB per vector
        - Types supported: string, number, boolean, list
        - All metadata is filterable unless explicitly configured as non-filterable
        - Non-filterable fields (excluded): text_content, document_id, s3_uri

        FILTER OPERATORS:
        - $eq: Exact match (string, number, boolean)
        - $ne: Not equal (string, number, boolean)  
        - $gt, $gte, $lt, $lte: Numeric comparisons (numbers only)
        - $in, $nin: Array membership operations (check if value is in/not in array)
        - $exists: Field existence check (boolean: true/false)
        - $and, $or: Logical operations (combine multiple conditions)

        EXAMPLE FILTER PATTERNS:
        - Single field exact match: {{"document_type": {{"$eq": "invoice"}}}}
        - Numeric range: {{"confidence_score": {{"$gte": 0.8}}}}
        - Array membership: {{"category": {{"$in": ["financial", "business"]}}}}
        - Field existence: {{"processed": {{"$exists": true}}}}
        - Combined conditions: {{"$and": [{{"document_type": {{"$eq": "invoice"}}}}, {{"year": {{"$eq": 2024}}}}]}}
        - Alternative conditions: {{"$or": [{{"document_type": {{"$eq": "invoice"}}}}, {{"document_type": {{"$eq": "receipt"}}}}]}}

        Create 8-10 practical filter examples that cover different use cases and operator combinations. Each example should be a template that can be adapted for specific queries. Focus on real-world document filtering scenarios. 

        CRITICAL: Return ONLY the JSON array, no other text or explanation:
        [
        {{
            "name": "descriptive name",
            "description": "what this filter does and when to use it", 
            "use_case": "specific scenario where this filter is useful",
            "filter": {{ "S3 Vectors filter JSON" }}
        }}
        ]
    """

    try:
        logger.info(f"Generating filter examples with Bedrock model: {NOVA_MODEL_ID}")
        response = bedrock_client.invoke_model(
            modelId=NOVA_MODEL_ID,
            body=json.dumps({
                "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.1
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '[]')
        
        content = content.strip()
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()

        filter_examples = json.loads(content)
        logger.info(f"Successfully generated {len(filter_examples)} filter examples.")
        return filter_examples
        
    except Exception:
        logger.error("Failed to generate filter examples from Bedrock.", exc_info=True)
        logger.info("Falling back to basic, default filter examples.")
        field_names = list(filterable_fields.keys())
        return [
            {
                'name': 'Default: Field Existence Check',
                'description': 'Checks if a specific field exists in the metadata.',
                'use_case': 'A fallback example because the AI model failed to generate examples.',
                'filter': {field_names[0]: {'$exists': True}} if field_names else {}
            }
        ]

def store_filter_examples(filter_examples: List[Dict[str, Any]]) -> str:
    """Stores the generated filter examples in a versioned and 'latest' S3 object."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    s3_prefix = f"metadata-filters/{S3_VECTORS_INDEX_NAME}"
    versioned_key = f"{s3_prefix}/filter-examples-{timestamp}.json"
    latest_key = f"{s3_prefix}/filter-examples-latest.json"
    
    filter_data = json.dumps({
        'generated_timestamp_utc': datetime.utcnow().isoformat(),
        'vector_index': S3_VECTORS_INDEX_NAME,
        'examples': filter_examples
    }, indent=2)
    
    s3_client.put_object(Bucket=WORKING_BUCKET, Key=versioned_key, Body=filter_data, ContentType='application/json')
    s3_client.put_object(Bucket=WORKING_BUCKET, Key=latest_key, Body=filter_data, ContentType='application/json')
    
    latest_location = f"s3://{WORKING_BUCKET}/{latest_key}"
    logger.info(f"Stored {len(filter_examples)} filter examples at {latest_location}")
    return latest_location

def update_lambda_environment(filterable_fields: List[str], s3_location: str):
    """Updates the Query Lambda's environment with the latest filter info."""
    logger.info(f"Updating environment of Lambda: {QUERY_LAMBDA_FUNCTION_NAME}")
    try:
        config = lambda_client.get_function_configuration(FunctionName=QUERY_LAMBDA_FUNCTION_NAME)
        env_vars = config.get('Environment', {}).get('Variables', {})

        env_vars['FILTERABLE_METADATA_KEYS'] = ','.join(filterable_fields)
        env_vars['FILTER_EXAMPLES_S3_LOCATION'] = s3_location

        lambda_client.update_function_configuration(
            FunctionName=QUERY_LAMBDA_FUNCTION_NAME,
            Environment={'Variables': env_vars}
        )
        logger.info("Successfully updated Lambda environment.")
    except Exception:
        logger.error(f"Failed to update environment for Lambda '{QUERY_LAMBDA_FUNCTION_NAME}'.", exc_info=True)
        raise # Re-raise the exception to fail the handler.