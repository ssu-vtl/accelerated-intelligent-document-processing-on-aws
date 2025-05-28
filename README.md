# Gen AI Intelligent Document Processing (GenAIIDP)

Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties

## Table of Contents

- [Introduction](#introduction)
  - [Key Features](#key-features)
  - [Use Cases](#use-cases)
- [Architecture](#architecture)
  - [Flow Overview](#flow-overview)
  - [Components](#components)
  - [Modular Design Overview](#modular-design-overview)
  - [Stack Structure](#stack-structure)
    - [Main Stack (template.yaml)](#main-stack-templateyaml)
    - [Pattern Stacks (patterns/*)](#pattern-stacks-patterns)
  - [Pattern Selection and Deployment](#pattern-selection-and-deployment)
  - [Integrated Monitoring](#integrated-monitoring)
  - [Adding New Patterns](#adding-new-patterns)
- [Build, Publish, Deploy, Test](#build-publish-deploy-test)
  - [Option 1: Deploy a new stack with 1-click launch (using pre-built assets)](#option-1-deploy-a-new-stack-with-1-click-launch-using-pre-built-assets)
  - [Option 2: Build deployment assets from source code](#option-2-build-deployment-assets-from-source-code)
    - [Dependencies](#dependencies)
    - [Build and Publish the solution](#build-and-publish-the-solution)
  - [Test the solution](#test-the-solution)
    - [Testing individual lambda functions locally](#testing-individual-lambda-functions-locally)
    - [Steady state volume testing using load simulator script](#steady-state-volume-testing-using-load-simulator-script)
    - [Variable volume testing using dynamic load simulator script](#variable-volume-testing-using-dynamic-load-simulator-script)
- [Web User Interface](#web-user-interface)
  - [Authentication Features](#authentication-features)
  - [Deploying the Web UI](#deploying-the-web-ui)
  - [Accessing the Web UI](#accessing-the-web-ui)
  - [Running the UI Locally](#running-the-ui-locally)
  - [Configuration Options](#configuration-options)
  - [Security Considerations](#security-considerations)
    - [Web Application Firewall (WAF)](#web-application-firewall-waf)
  - [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
- [Document Knowledge Base Query](#document-knowledge-base-query)
  - [How It Works](#how-it-works)
  - [Query Features](#query-features)
  - [Configuration](#configuration-2)
- [Evaluation Framework](#evaluation-framework)
  - [How It Works](#how-it-works-1)
  - [Configuration](#configuration-3)
  - [Viewing Reports](#viewing-reports)
  - [Best Practices](#best-practices)
  - [Metrics and Monitoring](#metrics-and-monitoring)
- [Configuration / Customization](#configuration--customization)
  - [Pattern Configuration via Web UI](#pattern-configuration-via-web-ui)
  - [Stack Parameters](#stack-parameters)
  - [Request Service Quota Limits for high volume processing](#request-service-quota-limits-for-high-volume-processing)
  - [Cost Estimation](#cost-estimation)
- [Customizing Classification](#customizing-classification)
  - [Classification Methods](#classification-methods)
  - [Classification Prompts](#classification-prompts)
  - [Using CachePoint for Classification](#using-cachepoint-for-classification)
  - [Document Classes](#document-classes)
- [Customizing Extraction](#customizing-extraction)
  - [Extraction Prompts](#extraction-prompts)
  - [Using CachePoint for Extraction](#using-cachepoint-for-extraction)
  - [Extraction Attributes](#extraction-attributes)
- [Monitoring and Logging](#monitoring-and-logging)
  - [CloudWatch Dashboard](#cloudwatch-dashboard)
    - [Latency Metrics](#latency-metrics)
    - [Throughput Metrics](#throughput-metrics)
    - [Error Tracking](#error-tracking)
  - [Log Groups](#log-groups)
- [Document Status Lookup](#document-status-lookup)
  - [Using the Lookup Script](#using-the-lookup-script)
  - [Response Format](#response-format)
- [Bedrock Guardrail Integration](#bedrock-guardrail-integration)
  - [How Guardrails Work](#how-guardrails-work)
  - [Configuring Guardrails](#configuring-guardrails)
  - [Best Practices](#best-practices-1)
- [Concurrency and Throttling Management](#concurrency-and-throttling-management)
  - [Throttling and Retry (Bedrock and/or SageMaker)](#throttling-and-retry-bedrock-andor-sagemaker)
  - [Step Functions Retry Configuration](#step-functions-retry-configuration)
  - [Concurrency Control](#concurrency-control)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Performance Considerations](#performance-considerations)
- [Additional scripts / utilities](#additional-scripts--utilities)


## Introduction

A scalable, serverless solution for automated document processing and information extraction using AWS services. This system combines OCR capabilities with generative AI to convert unstructured documents into structured data at scale.

### Key Features

- **Serverless Architecture**: Built entirely on AWS serverless technologies including Lambda, Step Functions, SQS, and DynamoDB, eliminating infrastructure management overhead
- **Modular, pluggable patterns for classification, splitting, extraction**: Pre-built processing patterns using the latest state of the art models and AWS services.. or create your own.
- **Advanced Classification Methods**: Support for both page-level and holistic document packet classification to handle complex multi-document inputs
- **Few Shot Example Support**: Improve accuracy through example-based prompting with concrete document examples and expected outputs for both classification and extraction tasks
- **High Throughput Processing**: Handles large volumes of documents through intelligent queuing and concurrency management
- **Built-in Resilience**: Features comprehensive error handling, automatic retries, and throttling management
- **Cost Optimization**: Pay-per-use pricing model with built-in controls and real-time cost estimation
- **Comprehensive Monitoring**: Rich CloudWatch dashboard with detailed metrics, logs, and alerts for end-to-end visibility
- **Easy Document Tracking**: Built-in tracking system to monitor document status and processing times
- **Secure by Design**: Implements encryption at rest, access controls, and secure communication between services
- **Web User Interface**: Secure, modern WebUI for inspecting document workflow status, inputs, and outputs
- **AI-Powered Evaluation**: Built-in framework to assess accuracy by comparing outputs against baseline data, with detailed AI-generated analysis reports
- **Document Knowledge Base Query**: Interactive tool to ask natural language questions about your processed document collection with AI-generated responses and source citations

### Use Cases

- Processing invoices, purchase orders, applications, and other document types
- Processing multi-document packets with automatic document boundary detection
- Extracting information from forms and applications
- Automating document-heavy workflows
- Converting legacy paper documents into structured digital data
- Real-time document processing pipelines
- Semantic querying of document collections for information retrieval
- Building knowledge bases from organizational documents

The system is designed to handle various document types and can be customized for specific extraction needs through configuration of the extraction prompts and attributes.

## Architecture

![Arch Diag](./images/IDP.drawio.png)

### Flow Overview
1. Documents uploaded to Input S3 bucket trigger EventBridge events
2. Queue Sender Lambda records event in tracking table and sends to SQS
3. Queue Processor Lambda:
   - Picks up messages in batches
   - Manages workflow concurrency using DynamoDB counter
   - Starts Step Functions executions
4. Step Functions workflow runs the steps defined in the selected pattern to process the document, and generate output in the Output S3 bucket.
5. Workflow completion events update tracking and metrics

### Components
- **Storage**: S3 buckets for input documents and JSON output
- **Message Queue**: Standard SQS queue for high throughput
- **Functions**: Lambda functions for queue operations
- **Step Functions**: Document processing workflow orchestration
- **DynamoDB**: Tracking and concurrency management
- **CloudWatch**: Comprehensive monitoring and logging

### Modular Design Overview

The solution uses a modular architecture with nested CloudFormation stacks to support multiple document processing patterns while maintaining a common infrastructure for queueing, tracking, and monitoring. This design enables:

- Support for multiple processing patterns without duplicating core infrastructure
- Easy addition of new processing patterns without modifying existing code
- Centralized monitoring and management across all patterns
- Pattern-specific optimizations and configurations

### Stack Structure

#### Main Stack (template.yaml)
The main template handles all pattern-agnostic resources and infrastructure:

- S3 Buckets (Input, Output)
- SQS Queues and Dead Letter Queues
- DynamoDB Tables (Execution Tracking, Concurrency)
- Lambda Functions for:
  - Queue Processing
  - Queue Sending
  - Workflow Tracking
  - Document Status Lookup
- CloudWatch Alarms and Dashboard
- SNS Topics for Alerts

#### Pattern Stacks (patterns/*)
Each pattern is implemented as a nested stack that contains pattern-specific resources:

- Step Functions State Machine
- Pattern-specific Lambda Functions:
  - OCR Processing
  - Classification
  - Extraction
- Pattern-specific CloudWatch Dashboard
- Model Endpoints and Configurations

Current patterns include:
- Pattern 1: Packet or Media processing with Bedrock Data Automation (BDA) ([README](./patterns/pattern-1/README.md))
- Pattern 2: OCR → Bedrock Classification (page-level or holistic) → Bedrock Extraction ([README](./patterns/pattern-2/README.md))
- Pattern 3: OCR → UDOP Classification (SageMaker) → Bedrock Extraction  ([README](./patterns/pattern-3/README.md))


### Pattern Selection and Deployment

The pattern is selected at deployment time using the `IDPPattern` parameter:

```yaml
IDPPattern:
  Type: String
  Default: Pattern2
  AllowedValues:
    - Pattern1  # Bedrock Data Automation (BDA)
    - Pattern2  # Textract + Bedrock (page-level or holistic classification)
    - Pattern3  # Textract + SageMaker UDOP + Bedrock
  Description: Choose from built-in IDP workflow patterns
```

Provide the additional parameter values specific to the selected pattern.

When deployed, the main stack uses conditions to create the appropriate nested stack:

```yaml
Conditions:
  IsPattern1: !Equals [!Ref IDPPattern, "Pattern1"]
  IsPattern2: !Equals [!Ref IDPPattern, "Pattern2"]
  IsPattern3: !Equals [!Ref IDPPattern, "Pattern3"]

Resources:
  PATTERN1STACK:
    Type: AWS::CloudFormation::Stack
    Condition: IsPattern1
    Properties:
      TemplateURL: ./patterns/pattern-1/.aws-sam/packaged.yaml
      Parameters:
        # Pattern-specific parameters...

  PATTERN2STACK:
    Type: AWS::CloudFormation::Stack
    Condition: IsPattern2
    Properties:
      TemplateURL: ./patterns/pattern-2/.aws-sam/packaged.yaml
      Parameters:
        # Pattern-specific parameters...

  etc..
```

### Integrated Monitoring

The solution creates an integrated CloudWatch dashboard that combines metrics from both the main stack and the selected pattern stack:

1. The main stack creates a dashboard with core metrics:
   - Queue performance
   - Overall workflow statistics
   - General error tracking
   - Resource utilization

2. Each pattern stack creates its own dashboard with pattern-specific metrics:
   - OCR performance
   - Classification accuracy
   - Extraction stats
   - Model-specific metrics

3. The `DashboardMerger` Lambda function combines these dashboards:
   ```yaml
   DashboardMergerFunction:
     Type: AWS::Serverless::Function
     Properties:
       Handler: index.handler
       Environment:
         Variables:
           STACK_NAME: !Ref AWS::StackName

   MergedDashboard:
     Type: Custom::DashboardMerger
     Properties:
       ServiceToken: !GetAtt DashboardMergerFunction.Arn
       Dashboard1Name: !Ref MainTemplateSubsetDashboard
       Dashboard2Name: !If 
         - IsPattern3
         - !GetAtt PATTERN1STACK.Outputs.DashboardName
         - !If
           - IsPattern2
           - !GetAtt PATTERN2STACK.Outputs.DashboardName
         etc.
       MergedDashboardName: !Sub "${AWS::StackName}-Integrated-${AWS::Region}"
   ```

The merger function:
- Reads the widgets from both dashboards
- Arranges them logically by type (time series, tables, etc.)
- Creates a new dashboard with the combined widgets
- Updates the integrated dashboard whenever either source dashboard changes

### Adding New Patterns

To add a new processing pattern:

1. Create a new directory under `patterns/`
2. Implement the pattern-specific resources in a CloudFormation template
3. Add the pattern to the `IDPPattern` parameter's allowed values
4. Add pattern-specific parameters to the main template
5. Create a new condition and nested stack resource for the pattern

The new pattern will automatically inherit all the core infrastructure and monitoring capabilities while maintaining its own specific processing logic and metrics.

## Build, Publish, Deploy, Test

If you're a developer, and you want to build, deploy, or publish the solution from code, go straight to [Option 2: Build deployment assets from source code](#option-2-build-deployment-assets-from-source-code), otherwise use Option 1 below.


### Option 1: Deploy a new stack with 1-click launch (using pre-built assets)

To deploy the GenAI-IDP solution in your own AWS account, follow these steps (if you do not have an AWS account, please see [How do I create and activate a new Amazon Web Services account?](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)):

1. Log into the [AWS console](https://console.aws.amazon.com/).
   _Note: If you are logged in as an IAM user, ensure your account has administrator permissions to create and manage the necessary resources and components for this application._
2. Choose the **Launch Stack** button below for your desired AWS region to open the AWS CloudFormation console and create a new stack:

| Region name           | Region code | Launch                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US West (Oregon)      | us-west-2   | [![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://s3.us-west-2.amazonaws.com/bobs-artifacts-us-west-2/genaiidp-preview-latest/idp-main.yaml&stackName=IDP) |


### Option 2: Build deployment assets from source code

#### Dependencies

You need to have the following packages installed on your computer:

1. bash shell (Linux, MacOS, Windows-WSL)
2. aws (AWS CLI)
3. [sam (AWS SAM)](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
4. python 3.11 or later
5. A local Docker daemon

Copy the repo to your computer. Either:
- use the git command to clone the repo, if you have access
- OR, download and expand the ZIP file for the repo, or use the ZIP file that has been shared with you.

#### Build and Publish the solution

To build and publish your own template, to your own S3 bucket, so that others can easily deploy a stack from your templates, in your preferred region, here's how.

* `cfn_bucket_basename`: A prefix added to the beginning of the bucket name (e.g. `idp-1234567890` to ensure that the resulting bucket name is globally unique) 
* `cfn_prefix`: A prefix added to Cloudformation resources. (e.g. `idp` or `idp-dev`)

Navigate into the project root directory and, in a bash shell, run:

`./publish.sh <cfn_bucket_basename> <cfn_prefix> <region e.g. us-east-1>`.  
  This:
    - checks your system dependencies for required packages (see Dependencies above)
    - creates CloudFormation templates and asset zip files
    - publishes the templates and required assets to an S3 bucket in your account called `<cfn_bucket_basename>-<region>` (it creates the bucket if it doesn't already exist)
    - e.g. `./publish.sh idp-1234567890 idp us-east-1`
    - optionally add a final parameter `public` if you want to make the published artifacts publicly accessible (e.g. `./publish.sh idp-1234567890 idp us-east-1 public`). Note: your bucket and account must be configured not to Block Public Access using new ACLs.

> * If the process throws an error `Docker daemon is not running` but Docker Desktop or similar is running, it may be necessary to examine the current docker context with the command `docker context ls`. 
> * In order to set the Docker context daemon, the `docker context use` command can be issued. e.g. `docker context use desktop-linux` if the desktop-linux context should be used.
> * It is also possible to set the `DOCKER_HOST` to the socket running the desired Docker daemon. e.g. `export DOCKER_HOST=unix:///Users/username/.docker/run/docker.sock`

**This completes the preparation stage of the installation process. The process now proceeds to the Cloudformation stack installation stage.**
  
When completed, it displays the CloudFormation template's S3 URL, and a 1-click URL for launching the stack creation in CloudFormation console:
```
OUTPUTS
Template URL: https://s3.<region>.amazonaws.com/<cfn_bucket_basename>-<region>/<cfn_prefix>/packaged.yaml
1-Click Launch URL: https://<region>.console.aws.amazon.com/cloudformation/home?region=<region>#/stacks/create/review?templateURL=https://s3.<region>.amazonaws.com/<cfn_bucket_basename>-<region>/<cfn_prefix>/packaged.yaml&stackName=IDP
Done
```

** Recommended: Deploy using AWS CloudFormation console.**  
For your first time deployment, log in to your AWS account and then use the `1-Click Launch URL` to create a new stack with CloudFormation. It's easier to inspect the available parameter options using the console initially. The CLI option below is better suited for scripted / automated deployments, and requires that you already know the right parameter values to use.

```bash
# To install from the CLI the `CLI Deploy` command will be similar to the following:
aws cloudformation deploy \
  --region <region> \
  --template-file <template-file> \
  --s3-bucket <bucket-name> \
  --s3-prefix <s3-prefix> \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides IDPPattern="<the-pattern-name-here>" AdminEmail=<your-email-here> \
  --stack-name <your-stack-name-here>
```

**CLI Deploy Notes:**
* `<the-pattern-name-here>` should be one of the valid pattern names encased in quotes. (Each pattern may have their own required parameter overrides, see README documentation for details.)
  * `Pattern1 - Packet or Media processing with Bedrock Data Automation (BDA)`
    * Can use an existing Bedrock Data Automation project, or can create a new demo BDA project for you to try with the samples/lending_package.pdf file.
  * `Pattern2 - Packet processing with Textract and Bedrock`
    * This pattern supports both page-level and holistic classification methods
    * This is a great pattern to start with to try out the solution because it has no further dependencies
  * `Pattern3 - Packet processing with Textract, SageMaker(UDOP), and Bedrock`
    * Requires a UDOP model in S3, that will be deployed on SageMaker during deployment.

After you have deployed the stack, check the Outputs tab to inspect names and links to the dashboards, buckets, workflows and other solution resources.

### Test the solution

Open the `S3InputBucketConsoleURL` and `S3OutputBucketConsoleURL` using the links in the stack Outputs tab.
Open the `StateMachineConsoleURL` using the link in the stack Outputs tab.

Upload a filled PDF form to the `InputBucket` - there's an example in the `./samples` folder.

Example - to copy the sample file `lending_package.pdf` N times, do:
```
$ n=10
$ for i in `seq 1 $n`; do aws s3 cp ./samples/lending_package.pdf s3://idp-inputbucket-kmsxxxxxxxxx/lending_package-$i.pdf; done
```

The StepFunctions StateMachine should start executing. Open the `Running` execution page to observe the steps in the workflow, trace inputs/outputs, check Lambda code and logs, etc.

When/if the execution successfully finishes, check the `OutputBucket` for the structured data JSON file with extracted fields.

### Testing individual lambda functions locally

For example, to test any lambda function locally:
- change directory to the folder that has the template.yaml for the function you want to test
- create a file containing the input event for your function.. some functions have templates in the ./testing folder 
- verify `./testing/env.json` and change region if necessary
- run `sam build` to package the function(s)
- use `sam local` to run the function locally in a container, e.g.:
``` 
sam local invoke OCRFunction -e testing/OCRFunction-event.json --env-vars testing/env.json
```

Follow similar process to test other lambda functions locally.


#### Steady state volume testing using load simulator script

Use `./scripts/simulate_load.py` to simulate heavy incoming document rates over time. It copies a specified source document from an S3 bucket, many times in parallel, to the designated `InputBucket`. Example - to simulate incoming document rate of 500 docs per minute for 10 minutes, do:
```
$ python ./scripts/simulate_load.py -s source_bucket -k prefix/exampledoc.pdf -d idp-kmsxxxxxxxxx -r 500 -t 10
```

#### Variable volume testing using dynamic load simulator script

Use `./scripts/simulate_dynamic_load.py` to simulate variable document rates over time. The rate of copying is determined by a CSV schedule file - e.g. [dynamic_schedule.csv](./scripts/dynamic_schedule.csv). It copies a specified source document from an S3 bucket, many times in parallel, to the designated `InputBucket`. Example - to simulate incoming documents based on the minute by minute rates in the schedule, do:
```
$ python ./scripts/simulate_load.py -s source_bucket -k prefix/exampledoc.pdf -d idp-kmsxxxxxxxxx -f schedule.csv
```


## Web User Interface

The solution includes a responsive web-based user interface built with React that provides:

- Document tracking and monitoring capabilities
- Real-time status updates of document processing
- Secure authentication using Amazon Cognito
- Searchable document history
- Detailed document processing metrics and status information
- Inspection of processing outputs for section classification and information extraction
- Accuracy evaluation reports, when baseline data is provided
- View and edit pattern configuration, including document classes, prompt engineering, and model settings
- Document upload from local computer  
- Knowledge base querying for document collections

<img src="./images/WebUI.png" alt="WebUI" width="800" style="border: 1px solid black;">

### Authentication Features

The web UI uses Amazon Cognito for secure user authentication and authorization:

- **User Management**: 
  - Admin users can be created during stack deployment
  - Optional self-service sign-up with email domain restrictions
  - Automatic email verification
  - Password policies and account recovery

- **Security Controls**:
  - Multi-factor authentication (MFA) support
  - Temporary credentials and automatic token refresh
  - Role-based access control using Cognito user groups
  - Secure session management

### Deploying the Web UI

The web UI is automatically deployed as part of the CloudFormation stack. The deployment:

1. Creates required Cognito resources (User Pool, Identity Pool)
2. Builds and deploys the React application to S3
3. Sets up CloudFront distribution for content delivery
4. Configures necessary IAM roles and permissions

### Accessing the Web UI

Once the stack is deployed:

1. Navigate to the `ApplicationWebURL` provided in the stack outputs
2. For first-time access:
   - Use the admin email address specified during stack deployment
   - Check your email for temporary credentials
   - You will be prompted to change your password on first login

### Running the UI Locally

To run the web UI locally for development:

1. Navigate to the `/ui` directory
2. Create a `.env` file using the `WebUITestEnvFile` output from the CloudFormation stack:
```
REACT_APP_USER_POOL_ID=<value>
REACT_APP_USER_POOL_CLIENT_ID=<value>
REACT_APP_IDENTITY_POOL_ID=<value>
REACT_APP_APPSYNC_GRAPHQL_URL=<value>
REACT_APP_AWS_REGION=<value>
REACT_APP_SETTINGS_PARAMETER=<value>
```
3. Install dependencies: `npm install`
4. Start the development server: `npm run start`
5. Open [http://localhost:3000](http://localhost:3000) in your browser

### Configuration Options

The following parameters are configured during stack deployment:

- `AdminEmail`: Email address for the admin user
- `AllowedSignUpEmailDomain`: Optional comma-separated list of allowed email domains for self-service signup

### Security Considerations

The web UI implementation includes several security features:

- All communication is encrypted using HTTPS
- Authentication tokens are automatically rotated
- Session timeouts are enforced
- CloudFront distribution uses secure configuration
- S3 buckets are configured with appropriate security policies
- API access is controlled through IAM and Cognito
- Web Application Firewall (WAF) protection for AppSync API

#### Web Application Firewall (WAF)

The solution includes AWS WAF integration to protect your AppSync API:

- **IP-based access control**: Restrict API access to specific IP ranges
- **Default behavior**: By default (`0.0.0.0/0`), WAF is disabled and all IPs are allowed
- **Configuration**: Use the `WAFAllowedIPv4Ranges` parameter to specify allowed IP ranges
  - Example: `"192.168.1.0/24,10.0.0.0/16"` (comma-separated list of CIDR blocks)
- **Security benefit**: When properly configured, WAF blocks all traffic except from your trusted IP ranges and AWS Lambda service IP ranges
- **Lambda service access**: The solution automatically maintains a WAF IPSet with current AWS Lambda service IP ranges to ensure Lambda functions can always access the AppSync API even when IP restrictions are enabled

When configuring the WAF:
- IP ranges must be in valid CIDR notation (e.g., `192.168.1.0/24`)
- Multiple ranges should be comma-separated
- The WAF is only enabled when the parameter is set to something other than the default `0.0.0.0/0`
- Lambda functions within your account will automatically have access to the AppSync API regardless of IP restrictions

### Monitoring and Troubleshooting

The web UI includes built-in monitoring:

- CloudWatch metrics for API and authentication activity
- Access logs in CloudWatch Logs
- CloudFront distribution logs
- Error tracking and reporting
- Performance monitoring

To troubleshoot issues:

1. Check CloudWatch Logs for application errors
2. Verify Cognito user status in the AWS Console
3. Check CloudFront distribution status
4. Verify API endpoints are accessible
5. Review browser console for client-side errors

## Document Knowledge Base Query

The solution includes an integrated Document Knowledge Base query feature that enables you to interactively ask questions about your processed document collection using natural language. This feature leverages the processed data to create a searchable knowledge base.

### How It Works

1. **Document Indexing**
   - Processed documents are automatically indexed in a vector database
   - Documents are chunked into semantic segments for efficient retrieval
   - Each chunk maintains reference to its source document

2. **Interactive Query Interface**
   - Access through the Web UI via the "Knowledge Base" section
   - Ask natural language questions about your document collection
   - View responses with citations to source documents
   - Follow-up with contextual questions in a chat-like interface

3. **AI-Powered Responses**
   - LLM generates responses based on relevant document chunks
   - Responses include citations to source documents
   - Links to original documents for reference
   - Context-aware for follow-up questions

### Query Features

- **Natural Language Understanding**: Ask questions in plain English rather than using keywords or query syntax
- **Document Citations**: Responses include references to the specific documents used to generate answers
- **Contextual Follow-ups**: Ask follow-up questions without repeating context
- **Direct Document Links**: Click on document references to view the original source
- **Markdown Formatting**: Responses support rich formatting for better readability
- **Real-time Processing**: Get answers in seconds, even across large document collections

### Configuration

The Document Knowledge Base Query feature can be configured during stack deployment:

```yaml
ShouldUseDocumentKnowledgeBase:
  Type: String
  Default: "true"
  AllowedValues:
    - "true"
    - "false"
  Description: Enable/disable the Document Knowledge Base feature

DocumentKnowledgeBaseModel:
  Type: String
  Default: "us.amazon.nova-pro-v1:0"
  Description: Bedrock model to use for knowledge base queries (e.g., "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
```

When the feature is enabled, the solution:
- Creates necessary OpenSearch resources for document indexing
- Configures API endpoints for querying the knowledge base
- Adds the query interface to the Web UI

## Evaluation Framework

The solution includes a built-in evaluation framework to assess the accuracy of document processing outputs. This allows you to:

- Compare processing outputs against baseline (ground truth) data
- Generate detailed evaluation reports using configurable methods and thresholds, including exact, fuzzy, semantic, and LLM powered comparisons. 
- Track and improve processing accuracy over time

### How It Works

1. **Baseline Data**
   - Store validated baseline data in a dedicated S3 bucket
   - Use an existing bucket or let the solution create one
   - Can use outputs from another GenAIIDP stack to compare different patterns/prompts

2. **Automatic Evaluation**
   - When enabled, automatically evaluates each processed document
   - Compares against baseline data if available
   - Generates detailed markdown reports using AI analysis

3. **Evaluation Reports**
   - Compare section classification accuracy
   - Analyze extracted field differences 
   - Identify patterns in discrepancies
   - Assess severity of differences (cosmetic vs. substantial)

### Configuration

Set the following parameters during stack deployment:

```yaml
EvaluationBaselineBucketName:
  Description: Existing bucket with baseline data, or leave empty to create new bucket
  
EvaluationAutoEnabled:
  Default: true
  Description: Automatically evaluate each document (if baseline exists)
  
EvaluationModelId:
  Default: "us.amazon.nova-pro-v1:0"
  Description: Model to use for evaluation reports (e.g., "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
```

### Viewing Reports

1. In the web UI, select a document from the Documents list
2. Click "View Evaluation Report" button 
3. The report shows:
   - Section classification accuracy
   - Field-by-field comparison 
   - Analysis of differences
   - Overall accuracy assessment

### Best Practices

- Enable auto-evaluation during testing/tuning phases
- Disable auto-evaluation in production for cost efficiency 
- Use evaluation reports to:
  - Compare different processing patterns
  - Test effects of prompt changes
  - Monitor accuracy over time
  - Identify areas for improvement

### Metrics and Monitoring

The evaluation framework includes comprehensive monitoring through CloudWatch metrics:

- **Evaluation Success/Failure Rates**: Track evaluation completion and error rates
- **Baseline Data Availability**: Monitor percentage of documents with baseline data for comparison
- **Report Generation Performance**: Track time to generate evaluation reports
- **Model Usage Metrics**: Monitor token consumption and API calls for evaluation models
- **Accuracy Trends**: Historical tracking of processing accuracy over time

## Configuration / Customization

The solution provides multiple configuration approaches to customize document processing behavior:

### Pattern Configuration via Web UI

The web interface allows real-time configuration updates without stack redeployment:

- **Document Classes**: Define and modify document categories and their descriptions
- **Extraction Attributes**: Configure fields to extract for each document class
- **Model Selection**: Choose between available Bedrock models for classification and extraction
- **Prompt Engineering**: Customize system and task prompts for optimal results
- **Few Shot Examples**: Upload and configure example documents to improve accuracy

Configuration changes are validated and applied immediately, with rollback capability if issues arise.

### Stack Parameters

Key parameters that can be configured during CloudFormation deployment:

- `IDPPattern`: Select processing pattern (Pattern1, Pattern2, Pattern3)
- `AdminEmail`: Administrator email for web UI access
- `MaxConcurrentWorkflows`: Control concurrent document processing
- `EvaluationAutoEnabled`: Enable automatic accuracy evaluation
- `ShouldUseDocumentKnowledgeBase`: Enable document querying features
- `WAFAllowedIPv4Ranges`: IP restrictions for web UI access

### Request Service Quota Limits for high volume processing

For high-volume document processing, consider requesting increases for these service quotas:

- **Lambda Concurrent Executions**: Default 1,000 per region
- **Step Functions Executions**: Default 25,000 per second
- **Bedrock Model Invocations**: Varies by model and region
- **SQS Message Rate**: Default 300 per second for FIFO queues
- **DynamoDB Read/Write Capacity**: Configure based on expected throughput

Use the AWS Service Quotas console to request increases before deploying for production workloads.

### Cost Estimation

The solution provides built-in cost estimation capabilities:

- Real-time cost tracking for Bedrock model usage
- Per-document processing cost breakdown
- Historical cost analysis and trends
- Budget alerts and threshold monitoring

See [COST_CALCULATOR.md](./COST_CALCULATOR.md) for detailed cost analysis across different processing volumes.

## Customizing Classification

Classification behavior can be customized through several mechanisms:

### Classification Methods

The solution supports multiple classification approaches:

1. **Page-Level Classification**: Classifies individual pages independently
2. **Holistic Packet Classification**: Analyzes entire document packets to identify boundaries
3. **Few Shot Classification**: Uses example documents to improve accuracy

### Classification Prompts

Customize classification behavior through:

- **System Prompts**: Define overall model behavior and constraints
- **Task Prompts**: Specify classification instructions and formatting
- **Class Descriptions**: Detailed descriptions for each document category
- **Few Shot Examples**: Reference documents with expected classifications

### Using CachePoint for Classification

The solution integrates with Amazon Bedrock CachePoint for improved performance:

- Caches frequently used prompts and responses
- Reduces latency for similar classification requests
- Optimizes costs through response reuse
- Automatic cache management and expiration

### Document Classes

Standard document classes based on RVL-CDIP dataset:

- `letter`: Formal written correspondence
- `form`: Structured documents with fields
- `email`: Digital messages with headers
- `handwritten`: Documents with handwritten content
- `advertisement`: Marketing materials
- `scientific_report`: Research documents
- `scientific_publication`: Academic papers
- `specification`: Technical specifications
- `file_folder`: Organizational documents
- `news_article`: Journalistic content
- `budget`: Financial planning documents
- `invoice`: Commercial billing documents
- `presentation`: Slide-based documents
- `questionnaire`: Survey forms
- `resume`: Employment documents
- `memo`: Internal communications

## Customizing Extraction

Information extraction can be tailored for specific document types and use cases:

### Extraction Prompts

Configure extraction behavior through:

- **Attribute Definitions**: Specify fields to extract per document class
- **Extraction Instructions**: Detailed guidance for field identification
- **Output Formatting**: Structure and validation requirements
- **Error Handling**: Fallback behavior for missing or unclear data

### Using CachePoint for Extraction

CachePoint integration for extraction provides:

- Cached extraction results for similar documents
- Improved consistency across similar document types
- Reduced processing costs and latency
- Automatic cache invalidation when prompts change

### Extraction Attributes

Common extraction attributes by document type:

**Invoice Documents:**
- `invoice_number`: Unique invoice identifier
- `invoice_date`: Date of invoice issuance
- `vendor_name`: Name of the invoicing company
- `total_amount`: Final amount due
- `due_date`: Payment deadline

**Form Documents:**
- `form_type`: Type or title of the form
- `applicant_name`: Name of person filling the form
- `date_submitted`: Form submission date
- `reference_number`: Form tracking number

**Letter Documents:**
- `sender_name`: Name of letter writer
- `recipient_name`: Name of letter recipient
- `date`: Letter date
- `subject`: Letter subject or topic

## Monitoring and Logging

The solution provides comprehensive monitoring through Amazon CloudWatch:

### CloudWatch Dashboard

The integrated dashboard displays:

#### Latency Metrics
- **End-to-End Processing Time**: Total time from document upload to completion
- **Step Function Execution Duration**: Time spent in workflow orchestration
- **Lambda Function Latency**: Processing time per function (OCR, Classification, Extraction)
- **Queue Wait Time**: Time documents spend in processing queues
- **Model Inference Time**: Bedrock model response latencies

#### Throughput Metrics
- **Documents Processed per Hour**: Overall system throughput
- **Pages Processed per Minute**: OCR processing rate
- **Classification Requests per Second**: Page classification throughput
- **Extraction Completions per Hour**: Field extraction processing rate
- **Queue Message Rate**: SQS message processing velocity

#### Error Tracking
- **Workflow Failures**: Step Function execution failures with error categorization
- **Lambda Timeouts**: Function timeout events and duration analysis
- **Model Throttling**: Bedrock throttling events and retry patterns
- **Dead Letter Queue Messages**: Failed messages requiring manual intervention
- **Validation Errors**: Data validation failures and format issues

### Log Groups

Centralized logging across all components:

- `/aws/stepfunctions/IDPWorkflow`: Step Function execution logs
- `/aws/lambda/QueueProcessor`: Document queue processing logs
- `/aws/lambda/OCRFunction`: OCR processing logs and errors
- `/aws/lambda/ClassificationFunction`: Classification processing logs
- `/aws/lambda/ExtractionFunction`: Extraction processing logs
- `/aws/lambda/TrackingFunction`: Document tracking and status logs
- `/aws/appsync/GraphQLAPI`: Web UI API access logs

All logs include correlation IDs for tracing individual document processing journeys.

## Document Status Lookup

The solution provides tools for tracking document processing status:

### Using the Lookup Script

Use the included script to check document processing status:

```bash
python scripts/document_status_lookup.py --stack-name <STACK_NAME> --document-key <DOCUMENT_KEY>
```

### Response Format

Status lookup returns comprehensive information:

```json
{
  "document_key": "example.pdf",
  "status": "COMPLETED",
  "workflow_arn": "arn:aws:states:...",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:05:30Z",
  "processing_time_seconds": 330,
  "pages_processed": 15,
  "sections_identified": 3,
  "output_location": "s3://output-bucket/results/example.json",
  "error_details": null
}
```

## Bedrock Guardrail Integration

The solution supports Amazon Bedrock Guardrails for content safety and compliance:

### How Guardrails Work

Guardrails provide:
- **Content Filtering**: Block harmful, inappropriate, or sensitive content
- **Topic Restrictions**: Prevent processing of specific topic areas
- **Data Protection**: Redact or block personally identifiable information (PII)
- **Custom Filters**: Define organization-specific content policies

### Configuring Guardrails

Enable guardrails through configuration:

```yaml
bedrock_settings:
  guardrail_id: "your-guardrail-id"
  guardrail_version: "1"
  enable_content_filtering: true
  enable_pii_detection: true
```

### Best Practices

1. **Test Thoroughly**: Validate guardrail behavior with representative documents
2. **Monitor Impact**: Track processing latency and accuracy changes
3. **Regular Updates**: Review and update guardrail policies as requirements evolve
4. **Compliance Alignment**: Ensure guardrails align with organizational compliance requirements

## Concurrency and Throttling Management

The solution implements sophisticated concurrency control and throttling management:

### Throttling and Retry (Bedrock and/or SageMaker)

- **Exponential Backoff**: Automatic retry with increasing delays
- **Jitter Addition**: Random delay variation to prevent thundering herd
- **Circuit Breaker**: Temporary halt on repeated failures
- **Rate Limiting**: Configurable request rate controls

### Step Functions Retry Configuration

```json
{
  "Retry": [
    {
      "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException"],
      "IntervalSeconds": 2,
      "MaxAttempts": 6,
      "BackoffRate": 2
    },
    {
      "ErrorEquals": ["States.TaskFailed"],
      "IntervalSeconds": 1,
      "MaxAttempts": 3,
      "BackoffRate": 2
    }
  ]
}
```

### Concurrency Control

- **Workflow Limits**: Maximum concurrent Step Function executions
- **Lambda Concurrency**: Per-function concurrent execution limits
- **Queue Management**: SQS visibility timeout and message batching
- **Dynamic Scaling**: Automatic adjustment based on queue depth

## Troubleshooting Guide

Common issues and resolution steps:

**Document Processing Failures:**
1. Check CloudWatch logs for specific error messages
2. Verify input document format and size limits
3. Confirm sufficient IAM permissions
4. Review Bedrock service quotas and throttling

**Web UI Access Issues:**
1. Verify Cognito user status and permissions
2. Check CloudFront distribution status
3. Confirm WAF IP allowlist configuration
4. Review browser console for client-side errors

**Performance Issues:**
1. Monitor CloudWatch dashboard for bottlenecks
2. Check Lambda function memory and timeout settings
3. Review Step Function execution patterns
4. Analyze queue depth and processing rates

**Configuration Problems:**
1. Validate configuration file syntax and schema
2. Test configuration changes in development environment
3. Review configuration validation logs
4. Confirm model availability in selected region

## Performance Considerations

Optimize performance through:

**Resource Sizing:**
- Lambda memory allocation based on document complexity
- Step Function timeout settings for large documents
- SQS batch size tuning for optimal throughput

**Concurrency Management:**
- Workflow concurrency limits to prevent service throttling
- Lambda reserved concurrency for critical functions
- Queue parallelism configuration

**Cost Optimization:**
- Model selection based on accuracy vs. cost requirements
- Caching strategies for repeated processing patterns
- Scheduled processing for non-urgent documents

**Monitoring:**
- Real-time performance dashboards
- Automated alerting for performance degradation
- Historical trend analysis for capacity planning

## Additional scripts / utilities
