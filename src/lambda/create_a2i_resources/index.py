# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import boto3
import os
import uuid
import urllib.request
import urllib.error

sagemaker = boto3.client('sagemaker')

def send_cfn_response(event, context, response_status, response_data, physical_resource_id=None, no_echo=False):
    """Send a response to CloudFormation to indicate success or failure"""
    response_url = event['ResponseURL']
    
    print(f"CFN response URL: {response_url}")
    
    response_body = {
        'Status': response_status,
        'Reason': f"See details in CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': physical_resource_id or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }
    
    json_response_body = json.dumps(response_body)
    
    print(f"Response body: {json_response_body}")
    
    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }
    
    try:
        response = urllib.request.Request(response_url, 
                                        data=json_response_body.encode('utf-8'),
                                        headers=headers,
                                        method='PUT')
        
        with urllib.request.urlopen(response) as response:
            print(f"Status code: {response.getcode()}")
            print(f"Status message: {response.msg}")
            
        return True
    except Exception as e:
        print(f"Error sending response to CloudFormation: {str(e)}")
        return False

def create_human_task_ui(stack_name):
    human_task_ui_name = f'{stack_name}-bda-hitl-template'
    ui_template_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Document Review</title>
        <script src="https://assets.crowd.aws/crowd-html-elements.js"></script>
        <style>
            :root {
                --primary-color: #2E5D7D;
                --secondary-color: #F8F9FA;
                --accent-color: #FFD700;
            }

            body { 
                font-family: 'Arial', sans-serif; 
                margin: 0;
                height: 100vh;
                overflow: hidden;
            }
            .container { 
                display: flex; 
                height: 100vh;
            }
            .image-pane { 
                width: 60%; 
                padding: 20px;
                background: #f0f2f5;
                overflow: hidden;
                position: relative;
            }
            .review-pane { 
                width: 40%; 
                padding: 20px;
                display: flex;
                flex-direction: column;
                background: white;
            }
            .scroll-container {
                flex: 1;
                overflow-y: auto;
                padding-right: 10px;
            }
            .zoom-controls { 
                margin-bottom: 15px;
                display: flex;
                gap: 10px;
            }
            .document-info { 
                background: var(--secondary-color); 
                padding: 20px; 
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .key-value-pair { 
                margin-bottom: 20px; 
                padding: 15px; 
                border: 1px solid #e9ecef; 
                border-radius: 6px; 
                background: white;
                transition: transform 0.2s ease;
                cursor: pointer;
            }
            #documentImage { 
                max-width: 100%; 
                max-height: calc(100vh - 100px);
                cursor: crosshair; 
                border-radius: 4px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .highlight-box {
                position: absolute;
                border: 2px solid var(--accent-color);
                background: rgba(255,215,0,0.15);
                pointer-events: none;
            }
            button {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                transition: opacity 0.2s;
            }
            button:hover { opacity: 0.85; }
            h3 { color: var(--primary-color); margin-top: 0; }
            .confidence-low { color: #dc3545; font-weight: 600; }
            .confidence-high { color: #28a745; font-weight: 600; }
        </style>
    </head>
    <body>
        <crowd-form>
            <div class="container">
                <!-- Image Pane -->
                <div class="image-pane">
                    <div class="zoom-controls">
                        <button type="button" onclick="zoom(1.1)">Zoom In (+)</button>
                        <button type="button" onclick="zoom(0.9)">Zoom Out (-)</button>
                    </div>
                    <img id="documentImage" 
                        src="{{ task.input.sourceDocument | grant_read_access }}" 
                        onload="initImage()">
                </div>

                <!-- Review Pane -->
                <div class="review-pane">
                    <div class="document-info">
                        <h3>Document Information</h3>
                        <p><strong>Current Blueprint:</strong> {{ task.input.blueprintName | escape }}</p>
                        <p><strong>Blueprint Confidence:</strong> {{ task.input.bp_confidence | round: 2 }}</p>
                        <p><strong>Confidence Threshold:</strong> {{ task.input.confidenceThreshold | round: 2 }}</p>
                        <p><strong>Page Number:</strong> {{ task.input.page_number }}</p>
                        <p><strong>Page Array:</strong> {{ task.input.page_array }}</p>
                        <p><strong>Execution ID:</strong> {{ task.input.execution_id }}</p>
                        <p><strong>Record ID:</strong> {{ task.input.record_id }}</p>

                        <!-- Dropdown for Blueprint Selection -->
                        <label for="blueprintSelection"><strong>Select Blueprint:</strong></label>
                        <select name="blueprintSelection" id="blueprintSelection" required disabled onchange="handleBlueprintChange()">
                            {% for option in task.input.blueprintOptions %}
                                <option value="{{ option.value | escape }}" {% if option.value == task.input.blueprintName %}selected{% endif %}>
                                    {{ option.label | escape }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>

                    <!-- Scrollable Key Value Section -->
                    <div class="scroll-container">
                        <h3>Key Value Review</h3>
                        {% for pair in task.input.keyValuePairs %}
                            {% assign bbox_index = forloop.index0 %}
                            <div class="key-value-pair" 
                                data-key="{{ pair.key | escape }}" 
                                data-bbox="{{ task.input.boundingBoxes[bbox_index].bounding_box | to_json | escape }}"
                                onclick="highlightBBox(this)">
                                <label>{{ pair.key | escape }}</label>
                                <crowd-input 
                                    name="{{ pair.key | escape }}" 
                                    value="{{ pair.value | escape }}"
                                    required>
                                </crowd-input>
                                <p class="confidence-{% if pair.confidence < task.input.confidenceThreshold %}low{% else %}high{% endif %}">
                                    Confidence: {{ pair.confidence | round: 2 }}
                                </p>
                                {% if pair.value == "" %}
                                    <p style="color: #dc3545; margin: 5px 0 0 0; font-size: 0.9em;">
                                        ⚠️ Value missing - please verify
                                    </p>
                                {% endif %}
                            </div>
                        {% endfor %}
                    </div>

                    <crowd-button 
                        form-action="submit" 
                        variant="primary" 
                        style="margin-top: 20px; align-self: flex-end;">
                        Submit Review
                    </crowd-button>
                </div>
            </div>
        </crowd-form>

        <script>
            let currentZoom = 1;
            let currentHighlight = null;
            const imgElement = document.getElementById('documentImage');
            let imgRect = null;

            function initImage() {
                imgRect = imgElement.getBoundingClientRect();
            }

            function zoom(factor) {
                currentZoom *= factor;
                imgElement.style.transform = `scale(${currentZoom})`;
                imgElement.style.transformOrigin = 'top left';
                imgRect = imgElement.getBoundingClientRect();
            }

            function highlightBBox(element) {
                if(currentHighlight) currentHighlight.remove();
                
                const bbox = JSON.parse(element.dataset.bbox || '{}');
                if(bbox?.width > 0 && bbox?.height > 0) {
                    currentHighlight = document.createElement('div');
                    currentHighlight.className = 'highlight-box';

                    const scaleX = imgElement.naturalWidth / imgElement.offsetWidth;
                    const scaleY = imgElement.naturalHeight / imgElement.offsetHeight;

                    currentHighlight.style.left = `${bbox.left * imgElement.offsetWidth + imgRect.left}px`;
                    currentHighlight.style.top = `${bbox.top * imgElement.offsetHeight + imgRect.top}px`;
                    currentHighlight.style.width = `${bbox.width * imgElement.offsetWidth}px`;
                    currentHighlight.style.height = `${bbox.height * imgElement.offsetHeight}px`;

                    document.body.appendChild(currentHighlight);
                }
            }

            function handleBlueprintChange() {
            const dropdown = document.getElementById("blueprintSelection");
            const selectedBlueprint = dropdown.value;

            // Get initial blueprint from the template
            const initialBlueprint = "{{ task.input.blueprintName }}";

            // Disable all key-value pairs if blueprint is changed
            const keyValuePairs = document.querySelectorAll(".key-value-pair");
            if (selectedBlueprint !== initialBlueprint) {
                keyValuePairs.forEach(pair => {
                    pair.classList.add("disabled");
                    const input = pair.querySelector("crowd-input");
                    input.setAttribute("disabled", "true");
                });
            } else {
                keyValuePairs.forEach(pair => {
                    pair.classList.remove("disabled");
                    const input = pair.querySelector("crowd-input");
                    input.removeAttribute("disabled");
                });
            }
        }

            document.addEventListener('click', (e) => {
                if(!e.target.closest('.key-value-pair') && currentHighlight) {
                    currentHighlight.remove();
                    currentHighlight = null;
                }
            });

            window.addEventListener('resize', () => {
                imgRect = imgElement.getBoundingClientRect();
            });
        </script>
    </body>
    </html>
    """

    try:
        response = sagemaker.create_human_task_ui(
            HumanTaskUiName=human_task_ui_name,
            UiTemplate={
                'Content': ui_template_content
            }
        )
        return response['HumanTaskUiArn']
    except Exception as e:
        print(f"Error creating HumanTaskUI: {e}")
        return None


def create_flow_definition(stack_name, human_task_ui_arn, a2i_workteam_arn, flow_definition_name):
    role_arn = os.environ.get('LAMBDA_EXECUTION_ROLE_ARN') #This needs to be explicitly passed
    try:
        response = sagemaker.create_flow_definition(
            FlowDefinitionName=flow_definition_name,
            HumanLoopConfig={
                'WorkteamArn': a2i_workteam_arn,
                'HumanTaskUiArn': human_task_ui_arn,
                'TaskTitle': 'Review Extracted Key Values',
                'TaskDescription': 'Review the key values extracted from the document.',
                'TaskCount': 1 
            },
            OutputConfig={
                'S3OutputPath': f's3://{os.environ["BDA_OUTPUT_BUCKET"]}/a2i-output' #Output to BDA Bucket
            },
            RoleArn=role_arn
        )
        return response['FlowDefinitionArn']
    except Exception as e:
        print(f"Error creating FlowDefinition: {e}")
        return None


def delete_human_task_ui(human_task_ui_name):
    try:
        sagemaker.delete_human_task_ui(HumanTaskUiName=human_task_ui_name)
        print(f"HumanTaskUI '{human_task_ui_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting HumanTaskUI '{human_task_ui_name}': {e}")


def delete_flow_definition(flow_definition_name):
    try:
        sagemaker.delete_flow_definition(FlowDefinitionName=flow_definition_name)
        print(f"Flow Definition '{flow_definition_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting Flow Definition '{flow_definition_name}': {e}")

def handler(event, context):
    stack_name = os.environ['STACK_NAME']
    a2i_workteam_arn = os.environ['A2I_WORKTEAM_ARN']
    human_task_ui_name = f'{stack_name}-bda-hitl-task'
    flow_definition_name = f'{stack_name}-bda-hitl-fd'
    ssm = boto3.client('ssm')
    
    # For debugging
    print(f"Event received: {json.dumps(event)}")
    
    response_data = {}
    
    try:
        # Handle CloudFormation lifecycle events
        if event.get('RequestType') == 'Create':
            print("Creating A2I Resources...")
            human_task_ui_arn = create_human_task_ui(stack_name)
            if human_task_ui_arn:
                flow_definition_arn = create_flow_definition(stack_name, human_task_ui_arn, a2i_workteam_arn,flow_definition_name)
                if flow_definition_arn:
                    # Store the Flow Definition ARN in SSM
                    ssm.put_parameter(
                        Name=f"/{stack_name}/FlowDefinitionArn",
                        Value=flow_definition_arn,
                        Type='String',
                        Overwrite=True
                    )
                    response_data['HumanTaskUiArn'] = human_task_ui_arn
                    response_data['FlowDefinitionArn'] = flow_definition_arn
                    send_cfn_response(event, context, 'SUCCESS', response_data)
                else:
                    print("Failed to create flow definition")
                    send_cfn_response(event, context, 'FAILED', {'Error': 'Failed to create flow definition'})
                    return
            else:
                print("Failed to create human task UI")
                send_cfn_response(event, context, 'FAILED', {'Error': 'Failed to create human task UI'})
                return
        
        elif event.get('RequestType') == 'Update':
            print("Updating A2I Resources...")
            delete_flow_definition(flow_definition_name)
            delete_human_task_ui(human_task_ui_name)
            
            human_task_ui_arn = create_human_task_ui(stack_name)
            if human_task_ui_arn:
                flow_definition_arn = create_flow_definition(stack_name, human_task_ui_arn, a2i_workteam_arn, flow_definition_name)
                if flow_definition_arn:
                    # Store the Flow Definition ARN in SSM
                    ssm.put_parameter(
                        Name=f"/{stack_name}/FlowDefinitionArn",
                        Value=flow_definition_arn,
                        Type='String',
                        Overwrite=True
                    )
                    response_data['HumanTaskUiArn'] = human_task_ui_arn
                    response_data['FlowDefinitionArn'] = flow_definition_arn
                    send_cfn_response(event, context, 'SUCCESS', response_data)
                else:
                    print("Failed to update flow definition")
                    send_cfn_response(event, context, 'FAILED', {'Error': 'Failed to update flow definition'})
                    return
            else:
                print("Failed to update human task UI")
                send_cfn_response(event, context, 'FAILED', {'Error': 'Failed to update human task UI'})
                return
                
        elif event.get('RequestType') == 'Delete':
            print("Deleting A2I Resources...")
            delete_flow_definition(flow_definition_name)
            delete_human_task_ui(human_task_ui_name)
            print("Success in deleting A2I resources")
            send_cfn_response(event, context, 'SUCCESS', {})
            return
            
        # In case RequestType is not provided or recognized
        else:
            print(f"Unknown RequestType: {event.get('RequestType')}")
            send_cfn_response(event, context, 'FAILED', {'Error': f"Unknown RequestType: {event.get('RequestType')}"})
            return
    except Exception as e:
        print(f"Error: {str(e)}")
        send_cfn_response(event, context, 'FAILED', {'Error': str(e)})
        return