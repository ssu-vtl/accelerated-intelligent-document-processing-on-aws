import boto3
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Initialize clients
_cloudwatch_client = None

def get_cloudwatch_client():
    """
    Get or initialize the CloudWatch client
    
    Returns:
        boto3 CloudWatch client
    """
    global _cloudwatch_client
    if _cloudwatch_client is None:
        _cloudwatch_client = boto3.client('cloudwatch')
    return _cloudwatch_client

def put_metric(name: str, value: float, unit: str = 'Count', 
              dimensions: Optional[List[Dict[str, str]]] = None,
              namespace: Optional[str] = None) -> None:
    """
    Publish a metric to CloudWatch
    
    Args:
        name: The name of the metric
        value: The value of the metric
        unit: The unit of the metric
        dimensions: Optional list of dimensions
        namespace: Optional metric namespace, defaults to environment variable
    """
    dimensions = dimensions or []
    
    # Get namespace from environment if not provided
    if namespace is None:
        namespace = os.environ.get('METRIC_NAMESPACE', 'GENAIDP')
    
    logger.info(f"Publishing metric {name}: {value}")
    try:
        cloudwatch = get_cloudwatch_client()
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[{
                'MetricName': name,
                'Value': value,
                'Unit': unit,
                'Dimensions': dimensions
            }]
        )
    except Exception as e:
        logger.error(f"Error publishing metric {name}: {e}")

def create_client_performance_metrics(name: str, duration_ms: float, 
                                     is_success: bool = True, 
                                     error_type: Optional[str] = None) -> None:
    """
    Helper to publish standardized client performance metrics
    
    Args:
        name: Base name for the metric group
        duration_ms: Duration in milliseconds
        is_success: Whether the operation succeeded
        error_type: Optional error type for failures
    """
    # Record latency
    put_metric(f"{name}Latency", duration_ms, 'Milliseconds')
    
    # Record success/failure
    if is_success:
        put_metric(f"{name}Success", 1)
    else:
        put_metric(f"{name}Failure", 1)
        if error_type:
            put_metric(f"{name}Error.{error_type}", 1)