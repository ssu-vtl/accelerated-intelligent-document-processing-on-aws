# transflo-idp

## Architecture Overview

The solution uses AWS services to create a serverless document processing pipeline:

```
S3 → EventBridge → Step Functions → Lambda → Textract/Bedrock → S3
```

### Components

1. **S3 Buckets**
   - Input: Receives documents for processing
   - Output: Stores extracted JSON results

2. **Step Functions Workflow**
   - Orchestrates document processing
   - Handles retries (5 attempts with exponential backoff)
   - Monitors execution status

3. **Lambda Functions**
   - Textract: Extracts text from documents
   - Bedrock: Uses Claude 3 Sonnet to extract structured data

4. **Monitoring**
   - CloudWatch Dashboard for operational visibility
   - Configurable alerts for errors and latency
   - Log retention and error tracking

The workflow triggers automatically when documents are uploaded to the input bucket, processes them through Textract and Claude, and saves structured JSON to the output bucket.

## Build, Publish, Deploy

### 1. Dependencies

You need to have the following packages installed on your computer:

1. bash shell (Linux, MacOS, Windows-WSL)
2. aws (AWS CLI)
3. sam (AWS SAM)

Copy the GitLab repo to your computer. Either:
- use the git command: git clone git@ssh.gitlab.aws.dev:genaiic-reusable-assets/transflo-idp.git
- OR, download and expand the ZIP file from the GitLab page: https://gitlab.aws.dev/genaiic-reusable-assets/transflo-idp/-/archive/main/transflo-idp-main.zip

## Build and Publish the solution

To build and publish your own template, to your own S3 bucket, so that others can easily deploy a stack from your templates, in your preferred region, here's how.

Navigate into the project root directory and, in a bash shell, run:

1. `./publish.sh <cfn_bucket_basename> <cfn_prefix> <region e.g. us-east-1>`.  
  This:
    - checks your system dependendencies for required packages (see Dependencies above)
    - creates CloudFormation templates and asset zip files
    - publishes the templates and required assets to an S3 bucket in your account called `<cfn_bucket_basename>-<region>` (it creates the bucket if it doesn't already exist)
    - optionally add a final parameter `public` if you want to make the templates public. Note: your bucket and account must be configured not to Block Public Access using new ACLs.

That's it! There's just one step.
  
When completed, it displays the CloudFormation templates S3 URLs, 1-click URLs for launching the stack creation in CloudFormation console, and a command to deploy from the CLI if preferred. E.g.:
```
OUTPUTS
Template URL: https://s3.us-east-1.amazonaws.com/bobs-artifacts-us-east-1/transflo-idp/packaged.yaml
CF Launch URL: https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?templateURL=https://s3.us-east-1.amazonaws.com/bobs-artifacts-us-east-1/transflo-idp/packaged.yaml&stackName=IDP
CLI Deploy: aws cloudformation deploy --region us-east-1 --template-file /tmp/1132557/packaged.yaml --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --stack-name IDP
Done
```

## Test the solution

Open the `InputBucket` and `OutputBucket` using the links in the stack Resources tab.
Open the `DocumentProcessingStateMachine` using the link in the stack Resources tab.

Upload a filled PNG or PDF form to the `InputBucket` - there's an example in the `./samples` folder.

Example - to copy the sample file `insurance-claim-form.png` N times, do:
```
$ n=50
$ for i in `seq 1 $n`; do aws s3 cp ./samples/insurance-claim-form.png s3://idp-inputbucket-kms4wmmc58rj/insurance-claim-form-$i.png; done
```

The StepFunctions StateMachine should start executing. Open the `Running` execution page to observe the steps in the workflow, trace inputs/outputs, check Lambda code and logs, etc.

When/if the execution sucessfully finishes, check the `OutputBucket` for the structured data JSON file with extracted fields.


# Monitoring and Logging

## CloudWatch Dashboard

Access via CloudWatch > Dashboards > DocumentProcessingDashboard

Shows:
1. Workflow Statistics
   - Execution counts (Started/Succeeded/Failed)
   - Average duration with configurable threshold line

2. Failed Workflow Executions
   - Lists most recent failures
   - Shows error details and execution ARNs

3. Lambda Function Performance
   - Textract Function:
     * Error logs with request IDs
     * Long-running invocations with duration and memory usage
   - Bedrock Function:
     * Error logs with request IDs
     * Long-running invocations with duration and memory usage

## Log Groups

```
/${StackName}/lambda/textract           # Textract function logs
/${StackName}/lambda/bedrock            # Bedrock function logs
/aws/vendedlogs/states/${StackName}-workflow  # Step Functions logs
```

## CloudWatch Alarms

Two alarms configured:
1. Workflow Errors (default: ≥1 error in 5 min)
2. Slow Executions (default: >30s)

Subscribe to alerts:
```bash
aws sns subscribe \
  --topic-arn <AlarmTopicARN> \
  --protocol email \
  --notification-endpoint your@email.com
```

## Stack Parameters

```bash
  LogRetentionDays=90 \        # Log retention (default: 30 days)
  ErrorThreshold=2 \           # Errors before alerting
  ExecutionTimeThresholdMs=45000  # Duration threshold (ms)
```

## Quick Troubleshooting

1. **Workflow Failures:** Check Failed Executions widget → use execution ARN in Step Functions console
2. **Lambda Issues:** 
   - Check dedicated error widgets for each function
   - Use request ID to trace through specific function logs
   - Review duration/memory metrics in long-running invocation widgets