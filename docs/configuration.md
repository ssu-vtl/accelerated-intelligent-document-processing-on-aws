# Configuration and Customization

The GenAIIDP solution provides multiple configuration approaches to customize document processing behavior to suit your specific needs.

## Pattern Configuration via Web UI

The web interface allows real-time configuration updates without stack redeployment:

- **Document Classes**: Define and modify document categories and their descriptions
- **Extraction Attributes**: Configure fields to extract for each document class
- **Model Selection**: Choose between available Bedrock models for classification and extraction
- **Prompt Engineering**: Customize system and task prompts for optimal results
- **Few Shot Examples**: Upload and configure example documents to improve accuracy

Configuration changes are validated and applied immediately, with rollback capability if issues arise.

## Stack Parameters

Key parameters that can be configured during CloudFormation deployment:

- `IDPPattern`: Select processing pattern (Pattern1, Pattern2, Pattern3)
- `AdminEmail`: Administrator email for web UI access
- `MaxConcurrentWorkflows`: Control concurrent document processing
- `EvaluationAutoEnabled`: Enable automatic accuracy evaluation
- `ShouldUseDocumentKnowledgeBase`: Enable document querying features
- `WAFAllowedIPv4Ranges`: IP restrictions for web UI access

## High Volume Processing

### Request Service Quota Limits

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

See [COST_CALCULATOR.md](../COST_CALCULATOR.md) for detailed cost analysis across different processing volumes.

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

## Additional Configuration Resources

The solution provides additional configuration options through:

- Configuration files in the `config_library` directory
- Pattern-specific settings in each pattern's subdirectory
- Environment variables for Lambda functions
- CloudWatch alarms and notification settings
