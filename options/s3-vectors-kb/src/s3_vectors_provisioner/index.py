import os
import json
import logging
import urllib3
from typing import Dict, Any

# Removed unused 'botocore' import
from idp_common.s3vectors.client import S3VectorsClient

# Initialize logger in the global scope for Lambda container reuse.
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

# Initialize S3VectorsClient lazily to avoid initialization errors at import time
s3vectors_client = None

def get_s3vectors_client():
    """Get or create S3VectorsClient instance"""
    global s3vectors_client
    if s3vectors_client is None:
        try:
            s3vectors_client = S3VectorsClient()
            logger.info("S3VectorsClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3VectorsClient: {e}", exc_info=True)
            raise
    return s3vectors_client

def provision_s3_vector_resources(
    vector_bucket_name: str, vector_index_name: str, dimension: int, distance_metric: str
) -> Dict[str, str]:
    """
    Idempotently creates an S3 Vector bucket and a corresponding index.

    Args:
        vector_bucket_name: The name of the S3 bucket to create.
        vector_index_name: The name of the vector index to create within the bucket.
        dimension: The dimensionality of the vectors that will be stored.
        distance_metric: The metric used to measure vector similarity (e.g., 'cosine').

    Returns:
        A dictionary containing the names of the created bucket and index.
    """
    logger.info(f"Provisioning resources: bucket='{vector_bucket_name}', index='{vector_index_name}'")
    client = get_s3vectors_client()
     
    client.create_bucket(vector_bucket_name)
    
    # Define non-filterable metadata keys (large content that shouldn't be used for filtering)

    client.create_index(
        vector_bucket_name,
        vector_index_name,
        dimension,
        distance_metric
        )
    
    
    return {'bucket': vector_bucket_name, 'index': vector_index_name}

def send_cfn_response(event: Dict[str, Any], context: Any, status: str, data: Dict, physical_resource_id: str = None):
    """
    Sends a standardized response to a CloudFormation pre-signed URL.
    """
    response_body = {
        'Status': status,
        'Reason': f"See CloudWatch Log Stream: {getattr(context, 'log_stream_name', 'unknown')}",
        'PhysicalResourceId': physical_resource_id or getattr(context, 'log_stream_name', 'unknown'),
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data,
    }

    logger.info(f"Sending CloudFormation response: {json.dumps(response_body)}")

    try:
        http = urllib3.PoolManager()
        response = http.request(
            'PUT',
            event['ResponseURL'],
            body=json.dumps(response_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        logger.info(f"CloudFormation response sent successfully. Status: {response.status}")
    except Exception as e:
        logger.error(f"Failed to send CloudFormation response: {e}", exc_info=True)

def handler(event: Dict[str, Any], context: Any):
    """
    CloudFormation Custom Resource handler for provisioning S3 Vector resources.
    """
    print('Started Provisioning')
    print(f'EVENT: {event}')
    request_type = event['RequestType']
    props = event.get('ResourceProperties', {})
    physical_id = event.get('PhysicalResourceId')

    logger.info(f"Received {request_type} request with properties: {json.dumps(props)}")

    try:
        if request_type == 'Delete':
            logger.info("Received Delete request. No-op to prevent data loss.")
            send_cfn_response(event, context, 'SUCCESS', {'message': 'no-op on delete'}, physical_resource_id=physical_id)
            return

        bucket = props['VectorBucketName']
        index = props['VectorIndexName']
        dimension = int(props.get('VectorDimension', 1024))
        distance_metric = props.get('DistanceMetric', 'cosine')

        result = provision_s3_vector_resources(bucket, index, dimension, distance_metric)

        new_physical_id = f"{result['bucket']}-{result['index']}"
        send_cfn_response(event, context, 'SUCCESS', result, physical_resource_id=new_physical_id)

    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        send_cfn_response(event, context, 'FAILED', {'error': str(e)}, physical_resource_id=physical_id or "failed-to-create")