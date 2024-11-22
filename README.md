# transflo-idp

### 1. Dependencies

To deploy or to publish, you need to have the following packages installed on your computer:

1. bash shell (Linux, MacOS, Windows-WSL)
2. aws (AWS CLI)
3. sam (AWS SAM)

Copy the GitLab repo to your computer. Either:
- use the git command: git clone git@ssh.gitlab.aws.dev:genaiic-reusable-assets/transflo-idp.git
- OR, download and expand the ZIP file from the GitLab page: https://gitlab.aws.dev/genaiic-reusable-assets/transflo-idp/-/archive/main/transflo-idp-main.zip

## Publish the solution

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
``````

## Test the solution

Open the `InputBucket` and `OutputBucket` using the links in the stack Resources tab.
Open the `DocumentProcessingStateMachine` using the link in the stack Resources tab.

Upload a filled PDF form to the `InputBucket`
- The StepFunctions StateMachine should start executing. Open the `Running` execution page to observe the steps in the workflow, trace inputs/outputs, check Lambda code and logs, etc.

When/if the execution sucessfully finishes, check the `OutputBucket` for the structured data JSON file with extracted fields.


## Monitoring & Alerts

### CloudWatch Dashboard

The solution includes a pre-configured CloudWatch Dashboard that provides visibility into the document processing workflow. 

**Dashboard Location:**  
CloudWatch > Dashboards > DocumentProcessingDashboard

**Key Metrics Displayed:**
* Workflow Execution Counts
  - Started executions
  - Successful executions  
  - Failed executions
* Execution Duration
  - Average processing time 
  - Red line indicates 30s threshold

### Alerts Configuration

The solution monitors two key conditions and sends notifications via SNS:

1. **Workflow Errors**
   - Triggers when any workflow execution fails
   - Evaluation period: 5 minutes
   - Threshold: ≥ 1 error

2. **Slow Executions** 
   - Triggers when average execution time exceeds 30 seconds
   - Evaluation period: 5 minutes
   - Alerts help identify performance degradation

### Setting Up Alert Notifications

1. Get the SNS Topic ARN from CloudFormation outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name doc-processing \
  --query 'Stacks[0].Outputs[?OutputKey==`AlertsTopicARN`].OutputValue' \
  --output text
```

2. Subscribe to alerts via email:
```bash
aws sns subscribe \
  --topic-arn <AlertsTopicARN> \
  --protocol email \
  --notification-endpoint your@email.com
```

3. Confirm the subscription by clicking the link in the verification email

### Configuring Alert Thresholds

The solution stack provides two configurable threshold parameters:

1. **ErrorThreshold**
   - Default: 1 error per 5 minutes
   - Minimum value: 1
   - Triggers alert when error count equals or exceeds this value

2. **ExecutionTimeThreshold**
   - Default: 30 seconds
   - Minimum value: 1
   - Triggers alert when average execution time exceeds this threshold

### Monitoring Best Practices

1. **Regular Dashboard Review**
   - Check execution trends
   - Look for patterns in failures
   - Monitor processing times

2. **Alert Response**
   - Document common error patterns
   - Set up escalation procedures
   - Review CloudWatch Logs for details when alerts trigger

3. **Performance Optimization**
   - Use execution time metrics to identify bottlenecks
   - Consider adjusting Lambda timeouts if needed
   - Monitor resource utilization

### Additional CloudWatch Insights

For deeper analysis, use CloudWatch Logs Insights with these example queries:

```sql
# Find all failed executions in last 24 hours
fields @timestamp, @message
| filter @message like /ExecutionsFailed/
| sort @timestamp desc
| limit 20

# Average execution time by hour
fields @timestamp, @message
| filter @message like /ExecutionTime/
| stats avg(ExecutionTime) by bin(1h)
```