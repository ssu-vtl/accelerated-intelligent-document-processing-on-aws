# Gen AI Intelligent Document Processing (GenAIIDP)

Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties

## Introduction

A scalable, serverless solution for automated document processing and information extraction using AWS services. This system combines OCR capabilities with generative AI to convert unstructured documents into structured data at scale.

## Key Features

- **Serverless Architecture**: Built entirely on AWS serverless technologies including Lambda, Step Functions, SQS, and DynamoDB
- **Modular, pluggable patterns**: Pre-built processing patterns using state-of-the-art models and AWS services
- **Advanced Classification**: Support for page-level and holistic document packet classification
- **Few Shot Example Support**: Improve accuracy through example-based prompting
- **High Throughput Processing**: Handles large volumes of documents through intelligent queuing
- **Built-in Resilience**: Comprehensive error handling, retries, and throttling management
- **Cost Optimization**: Pay-per-use pricing model with built-in controls
- **Comprehensive Monitoring**: Rich CloudWatch dashboard with detailed metrics and logs
- **Web User Interface**: Modern UI for inspecting document workflow status and results
- **AI-Powered Evaluation**: Framework to assess accuracy against baseline data
- **Document Knowledge Base Query**: Ask questions about your processed documents

## Architecture Overview

![Architecture Diagram](./images/IDP.drawio.png)

The solution uses a modular architecture with nested CloudFormation stacks to support multiple document processing patterns while maintaining common infrastructure for queueing, tracking, and monitoring.

Current patterns include:
- Pattern 1: Packet or Media processing with Bedrock Data Automation (BDA)
- Pattern 2: OCR → Bedrock Classification (page-level or holistic) → Bedrock Extraction
- Pattern 3: OCR → UDOP Classification (SageMaker) → Bedrock Extraction

## Detailed Documentation

- [Architecture](./docs/architecture.md) - Detailed component architecture and data flow
- [Deployment](./docs/deployment.md) - Build, publish, deploy, and test instructions
- [Web UI](./docs/web-ui.md) - Web interface features and usage
- [Knowledge Base](./docs/knowledge-base.md) - Document knowledge base query feature
- [Evaluation Framework](./docs/evaluation.md) - Accuracy assessment system
- [Configuration](./docs/configuration.md) - Configuration and customization options
- [Classification](./docs/classification.md) - Customizing document classification
- [Extraction](./docs/extraction.md) - Customizing information extraction
- [Monitoring](./docs/monitoring.md) - Monitoring and logging capabilities
- [Troubleshooting](./docs/troubleshooting.md) - Troubleshooting and performance guides

## Quick Start

To quickly deploy the GenAI-IDP solution in your AWS account:

1. Log into the [AWS console](https://console.aws.amazon.com/)
2. Choose the **Launch Stack** button below for your desired region:

| Region name           | Region code | Launch                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US West (Oregon)      | us-west-2   | [![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://s3.us-west-2.amazonaws.com/bobs-artifacts-us-west-2/genaiidp-preview-latest/idp-main.yaml&stackName=IDP) |

For detailed deployment instructions, see the [Deployment Guide](./docs/deployment.md).

## License

This project is licensed under the terms specified in the LICENSE file.
