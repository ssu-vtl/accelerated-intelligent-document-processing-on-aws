# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
import logging
import time
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to trigger ad-hoc HITL for Pattern-1 documents
    """
    try:
        # Parse the request
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        document_id = body.get('document_id')
        confidence_threshold = body.get('confidence_threshold', 0.8)
        force_hitl = body.get('force_hitl', False)
        
        if not document_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'document_id is required'})
            }
        
        # Get document from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DOCUMENT_TABLE'])
        
        response = table.get_item(Key={'id': document_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'Document not found'})
            }
        
        document = response['Item']
        
        # Check if HITL should be triggered
        should_trigger = force_hitl or check_confidence_threshold(document, confidence_threshold)
        
        if should_trigger:
            # Trigger HITL workflow
            result = trigger_hitl_workflow(document, confidence_threshold)
            
            # Update document status
            update_document_hitl_status(document_id, True, confidence_threshold)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'message': 'HITL workflow triggered successfully',
                    'document_id': document_id,
                    'hitl_job_id': result.get('hitl_job_id'),
                    'confidence_threshold': confidence_threshold
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'message': 'Document confidence is above threshold, HITL not triggered',
                    'document_id': document_id,
                    'confidence_threshold': confidence_threshold
                })
            }
            
    except Exception as e:
        logger.error(f"Error in HITL invocation: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def lambda_handler_options(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': ''
    }

def check_confidence_threshold(document: Dict[str, Any], threshold: float) -> bool:
    """Check if document confidence is below threshold"""
    try:
        # Extract confidence information from document
        sections = document.get('sections', [])
        
        for section in sections:
            attributes = section.get('attributes', {})
            
            # Check blueprint confidence
            bp_confidence = attributes.get('bp_confidence')
            if bp_confidence and float(bp_confidence) < threshold:
                logger.info(f"Blueprint confidence {bp_confidence} below threshold {threshold}")
                return True
            
            # Check key-value confidences from explainability data
            explainability_info = section.get('explainability_info', [])
            for explain_data in explainability_info:
                if isinstance(explain_data, dict):
                    for key, value in explain_data.items():
                        if isinstance(value, dict) and 'confidence' in value:
                            if float(value['confidence']) < threshold:
                                logger.info(f"Key-value confidence for {key}: {value['confidence']} below threshold {threshold}")
                                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking confidence threshold: {str(e)}")
        return False

def trigger_hitl_workflow(document: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """Trigger the HITL workflow for the document"""
    try:
        # For now, we'll simulate HITL triggering by updating the document
        # In a full implementation, this would start a Step Functions execution
        # or invoke SageMaker A2I directly
        
        logger.info(f"Triggering HITL for document {document['id']} with threshold {threshold}")
        
        # Simulate HITL job creation
        hitl_job_id = f"hitl-{document['id']}-{int(time.time())}"
        
        return {
            'hitl_job_id': hitl_job_id,
            'status': 'started'
        }
        
    except Exception as e:
        logger.error(f"Error triggering HITL workflow: {str(e)}")
        raise

def update_document_hitl_status(document_id: str, hitl_triggered: bool, threshold: float):
    """Update document with HITL status"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DOCUMENT_TABLE'])
        
        table.update_item(
            Key={'id': document_id},
            UpdateExpression='SET hitl_triggered = :hitl, confidence_threshold_used = :threshold, updated_at = :timestamp',
            ExpressionAttributeValues={
                ':hitl': hitl_triggered,
                ':threshold': threshold,
                ':timestamp': int(time.time())
            }
        )
        
        logger.info(f"Updated document {document_id} with HITL status: {hitl_triggered}")
        
    except Exception as e:
        logger.error(f"Error updating document HITL status: {str(e)}")
        raise
