#!/usr/bin/env python3
"""
Enhancement script to add Pattern-1 confidence threshold support to UI configuration
and enable dynamic HITL invocation.
"""

import yaml
import json
import os

def enhance_pattern1_config():
    """Add confidence threshold configuration to Pattern-1 config"""
    
    # Read current Pattern-1 config
    config_path = "config_library/pattern-1/default/config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Add confidence threshold configuration section
    config['confidence'] = {
        'overall_threshold': 0.8,  # Default threshold, will be overridden by CloudFormation parameter
        'description': 'Overall confidence threshold for BDA processing. If the blueprint confidence or any key-value confidence falls below this threshold, HITL will be triggered.',
        'ui_display': {
            'label': 'Confidence Threshold',
            'description': 'Minimum confidence score required to avoid human review',
            'type': 'slider',
            'min': 0.0,
            'max': 1.0,
            'step': 0.05,
            'format': 'percentage'
        }
    }
    
    # Add HITL configuration section
    config['hitl'] = {
        'enabled': True,  # Will be overridden by CloudFormation parameter
        'description': 'Human In The Loop configuration for Pattern-1',
        'trigger_conditions': [
            'blueprint_confidence_below_threshold',
            'keyvalue_confidence_below_threshold'
        ],
        'ui_display': {
            'show_confidence_scores': True,
            'highlight_low_confidence': True,
            'color_coding': {
                'high_confidence': '#16794d',  # Green
                'medium_confidence': '#ff9500',  # Orange  
                'low_confidence': '#d13313'  # Red
            }
        }
    }
    
    # Write updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Enhanced {config_path} with confidence threshold configuration")

def create_pattern1_ui_config():
    """Create UI configuration schema for Pattern-1"""
    
    ui_config = {
        "pattern": "pattern-1",
        "version": "1.0",
        "display_name": "BDA Processing with HITL",
        "description": "Bedrock Data Automation processing with Human In The Loop support",
        "sections": [
            {
                "id": "confidence_settings",
                "title": "Confidence & HITL Settings",
                "description": "Configure confidence thresholds and human review settings",
                "fields": [
                    {
                        "id": "overall_threshold",
                        "label": "Overall Confidence Threshold",
                        "description": "Minimum confidence score required to avoid human review. Applies to both blueprint matching and key-value extraction.",
                        "type": "slider",
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "default": 0.8,
                        "format": "percentage",
                        "config_path": "confidence.overall_threshold",
                        "validation": {
                            "required": True,
                            "min": 0.1,
                            "max": 1.0
                        }
                    },
                    {
                        "id": "hitl_enabled",
                        "label": "Enable Human In The Loop",
                        "description": "When enabled, documents with confidence below threshold will be sent for human review",
                        "type": "toggle",
                        "default": True,
                        "config_path": "hitl.enabled"
                    }
                ]
            },
            {
                "id": "summarization_settings", 
                "title": "Summarization Settings",
                "description": "Configure document summarization parameters",
                "fields": [
                    {
                        "id": "model",
                        "label": "Summarization Model",
                        "description": "Select the model for document summarization",
                        "type": "select",
                        "options": [
                            {"value": "us.amazon.nova-lite-v1:0", "label": "Nova Lite"},
                            {"value": "us.amazon.nova-pro-v1:0", "label": "Nova Pro"},
                            {"value": "us.amazon.nova-premier-v1:0", "label": "Nova Premier"}
                        ],
                        "default": "us.amazon.nova-premier-v1:0",
                        "config_path": "summarization.model"
                    },
                    {
                        "id": "temperature",
                        "label": "Temperature",
                        "description": "Controls randomness in text generation (0.0 = deterministic, 1.0 = very random)",
                        "type": "slider",
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1,
                        "default": 0.0,
                        "config_path": "summarization.temperature"
                    }
                ]
            }
        ],
        "confidence_display": {
            "enabled": True,
            "type": "overall",  # Different from pattern-2 which uses "attribute_level"
            "thresholds": {
                "high": 0.9,
                "medium": 0.7,
                "low": 0.5
            },
            "colors": {
                "high": "#16794d",
                "medium": "#ff9500", 
                "low": "#d13313"
            },
            "show_scores": True,
            "show_threshold_line": True
        }
    }
    
    # Create UI config directory if it doesn't exist
    ui_config_dir = "config_library/pattern-1/default/ui"
    os.makedirs(ui_config_dir, exist_ok=True)
    
    # Write UI configuration
    ui_config_path = f"{ui_config_dir}/config.json"
    with open(ui_config_path, 'w') as f:
        json.dump(ui_config, f, indent=2)
    
    print(f"Created UI configuration at {ui_config_path}")

def create_confidence_utils_for_pattern1():
    """Create Pattern-1 specific confidence utilities"""
    
    js_utils = '''// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * Pattern-1 specific confidence utilities for BDA processing
 */

/**
 * Get overall confidence information for Pattern-1 documents
 * @param {Object} document - Document object
 * @param {number} confidenceThreshold - Overall confidence threshold
 * @returns {Object} Confidence information with display properties
 */
export const getPattern1ConfidenceInfo = (document, confidenceThreshold = 0.8) => {
  if (!document || !document.sections || !Array.isArray(document.sections)) {
    return { hasConfidenceInfo: false };
  }

  // For Pattern-1, we look at overall document confidence
  // This includes blueprint confidence and key-value confidences
  let overallConfidence = null;
  let blueprintConfidence = null;
  let keyValueConfidences = [];
  let hitlTriggered = false;

  // Extract confidence information from document sections
  document.sections.forEach(section => {
    if (section.attributes) {
      // Look for blueprint confidence
      if (section.attributes.extraction_bp_name && section.attributes.bp_confidence) {
        blueprintConfidence = parseFloat(section.attributes.bp_confidence);
      }
      
      // Look for HITL status
      if (section.attributes.hitl_triggered !== undefined) {
        hitlTriggered = section.attributes.hitl_triggered;
      }
      
      // Extract key-value confidences from explainability data
      if (section.explainability_info && Array.isArray(section.explainability_info)) {
        section.explainability_info.forEach(explainData => {
          if (explainData && typeof explainData === 'object') {
            Object.entries(explainData).forEach(([key, value]) => {
              if (value && typeof value === 'object' && typeof value.confidence === 'number') {
                keyValueConfidences.push({
                  field: key,
                  confidence: value.confidence,
                  threshold: confidenceThreshold
                });
              }
            });
          }
        });
      }
    }
  });

  // Calculate overall confidence (minimum of blueprint and key-value confidences)
  const allConfidences = [];
  if (blueprintConfidence !== null) {
    allConfidences.push(blueprintConfidence);
  }
  keyValueConfidences.forEach(kv => allConfidences.push(kv.confidence));
  
  if (allConfidences.length > 0) {
    overallConfidence = Math.min(...allConfidences);
  }

  if (overallConfidence === null) {
    return { hasConfidenceInfo: false };
  }

  const isAboveThreshold = overallConfidence >= confidenceThreshold;
  
  return {
    hasConfidenceInfo: true,
    overallConfidence,
    blueprintConfidence,
    keyValueConfidences,
    confidenceThreshold,
    isAboveThreshold,
    hitlTriggered,
    shouldHighlight: !isAboveThreshold || hitlTriggered,
    textColor: getConfidenceColor(overallConfidence, confidenceThreshold),
    displayMode: 'overall-confidence',
    confidenceLevel: getConfidenceLevel(overallConfidence, confidenceThreshold)
  };
};

/**
 * Get color based on confidence score and threshold
 * @param {number} confidence - Confidence score
 * @param {number} threshold - Confidence threshold
 * @returns {string} Color code
 */
export const getConfidenceColor = (confidence, threshold) => {
  if (confidence >= threshold) {
    return '#16794d'; // Green - good confidence
  } else if (confidence >= threshold * 0.8) {
    return '#ff9500'; // Orange - medium confidence
  } else {
    return '#d13313'; // Red - low confidence
  }
};

/**
 * Get confidence level description
 * @param {number} confidence - Confidence score
 * @param {number} threshold - Confidence threshold
 * @returns {string} Confidence level
 */
export const getConfidenceLevel = (confidence, threshold) => {
  if (confidence >= threshold) {
    return 'high';
  } else if (confidence >= threshold * 0.8) {
    return 'medium';
  } else {
    return 'low';
  }
};

/**
 * Check if document should trigger HITL based on confidence
 * @param {Object} document - Document object
 * @param {number} confidenceThreshold - Confidence threshold
 * @returns {boolean} Whether HITL should be triggered
 */
export const shouldTriggerHITL = (document, confidenceThreshold) => {
  const confidenceInfo = getPattern1ConfidenceInfo(document, confidenceThreshold);
  return confidenceInfo.hasConfidenceInfo && !confidenceInfo.isAboveThreshold;
};

/**
 * Format confidence score for display
 * @param {number} confidence - Confidence score
 * @param {boolean} asPercentage - Whether to format as percentage
 * @returns {string} Formatted confidence score
 */
export const formatConfidenceScore = (confidence, asPercentage = true) => {
  if (typeof confidence !== 'number') {
    return 'N/A';
  }
  
  if (asPercentage) {
    return `${(confidence * 100).toFixed(1)}%`;
  } else {
    return confidence.toFixed(3);
  }
};
'''
    
    # Create the utility file
    utils_dir = "src/ui/src/components/common"
    os.makedirs(utils_dir, exist_ok=True)
    
    utils_path = f"{utils_dir}/pattern1-confidence-utils.js"
    with open(utils_path, 'w') as f:
        f.write(js_utils)
    
    print(f"Created Pattern-1 confidence utilities at {utils_path}")

def create_hitl_invocation_lambda():
    """Create Lambda function for ad-hoc HITL invocation"""
    
    lambda_code = '''# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import os
import logging
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
                'body': json.dumps({'error': 'document_id is required'})
            }
        
        # Get document from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DOCUMENT_TABLE'])
        
        response = table.get_item(Key={'id': document_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
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
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
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
                return True
            
            # Check key-value confidences from explainability data
            explainability_info = section.get('explainability_info', [])
            for explain_data in explainability_info:
                if isinstance(explain_data, dict):
                    for key, value in explain_data.items():
                        if isinstance(value, dict) and 'confidence' in value:
                            if float(value['confidence']) < threshold:
                                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking confidence threshold: {str(e)}")
        return False

def trigger_hitl_workflow(document: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """Trigger the HITL workflow for the document"""
    try:
        # Start Step Functions execution for HITL
        stepfunctions = boto3.client('stepfunctions')
        
        hitl_input = {
            'document_id': document['id'],
            'confidence_threshold': threshold,
            'trigger_reason': 'ad_hoc_request',
            'document_data': document
        }
        
        response = stepfunctions.start_execution(
            stateMachineArn=os.environ['HITL_STATE_MACHINE_ARN'],
            name=f"hitl-{document['id']}-{int(time.time())}",
            input=json.dumps(hitl_input)
        )
        
        return {
            'hitl_job_id': response['executionArn'],
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
        
    except Exception as e:
        logger.error(f"Error updating document HITL status: {str(e)}")
        raise

import time
'''
    
    # Create the Lambda function directory
    lambda_dir = "src/lambda/hitl_invocation"
    os.makedirs(lambda_dir, exist_ok=True)
    
    # Write the Lambda function
    lambda_path = f"{lambda_dir}/index.py"
    with open(lambda_path, 'w') as f:
        f.write(lambda_code)
    
    print(f"Created HITL invocation Lambda at {lambda_path}")

def update_pattern1_template():
    """Update Pattern-1 template to support dynamic confidence threshold"""
    
    template_additions = '''
  # Add HITL invocation Lambda function
  HITLInvocationFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ../../src/lambda/hitl_invocation/
      Handler: index.lambda_handler
      Runtime: python3.11
      Timeout: 300
      Environment:
        Variables:
          DOCUMENT_TABLE: !Ref DocumentTable
          HITL_STATE_MACHINE_ARN: !Ref HITLStateMachine
          LOG_LEVEL: !Ref LogLevel
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref DocumentTable
        - StepFunctionsExecutionPolicy:
            StateMachineName: !GetAtt HITLStateMachine.Name
        - Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: "*"

  # API Gateway for HITL invocation
  HITLInvocationApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: Prod
      Cors:
        AllowMethods: "'POST, OPTIONS'"
        AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
        AllowOrigin: "'*'"

  HITLInvocationApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ../../src/lambda/hitl_invocation/
      Handler: index.lambda_handler
      Runtime: python3.11
      Events:
        HITLInvocationApi:
          Type: Api
          Properties:
            RestApiId: !Ref HITLInvocationApi
            Path: /trigger-hitl
            Method: post

  # Step Functions state machine for HITL workflow
  HITLStateMachine:
    Type: AWS::StepFunctions::StateMachine
    Properties:
      StateMachineName: !Sub "${AWS::StackName}-HITL-Workflow"
      DefinitionString: !Sub |
        {
          "Comment": "HITL workflow for Pattern-1 documents",
          "StartAt": "ProcessHITLRequest",
          "States": {
            "ProcessHITLRequest": {
              "Type": "Task",
              "Resource": "${HITLProcessFunction.Arn}",
              "Next": "WaitForHumanReview"
            },
            "WaitForHumanReview": {
              "Type": "Task", 
              "Resource": "${HITLWaitFunction.Arn}",
              "Next": "ProcessHITLResults"
            },
            "ProcessHITLResults": {
              "Type": "Task",
              "Resource": "${HITLResultsFunction.Arn}",
              "End": true
            }
          }
        }
      RoleArn: !GetAtt HITLStateMachineRole.Arn

  HITLStateMachineRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: states.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: HITLStateMachinePolicy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - lambda:InvokeFunction
                Resource:
                  - !GetAtt HITLProcessFunction.Arn
                  - !GetAtt HITLWaitFunction.Arn
                  - !GetAtt HITLResultsFunction.Arn

Outputs:
  HITLInvocationApiUrl:
    Description: "API Gateway endpoint URL for HITL invocation"
    Value: !Sub "https://${HITLInvocationApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/trigger-hitl"
    Export:
      Name: !Sub "${AWS::StackName}-HITLInvocationApiUrl"
'''
    
    print("Template additions for HITL invocation API created")
    print("Note: These additions should be manually integrated into patterns/pattern-1/template.yaml")

if __name__ == "__main__":
    print("Enhancing Pattern-1 with confidence threshold and HITL support...")
    
    enhance_pattern1_config()
    create_pattern1_ui_config()
    create_confidence_utils_for_pattern1()
    create_hitl_invocation_lambda()
    update_pattern1_template()
    
    print("\n✅ Pattern-1 enhancement complete!")
    print("\nNext steps:")
    print("1. Review and integrate the template additions into patterns/pattern-1/template.yaml")
    print("2. Update the UI components to use the new Pattern-1 confidence utilities")
    print("3. Test the confidence threshold configuration in the UI")
    print("4. Test ad-hoc HITL invocation through the API")
