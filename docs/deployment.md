# GenAIIDP Deployment Guide

This guide covers how to deploy, build, publish, and test the GenAI Intelligent Document Processing solution.

## Deployment Options

There are two ways to deploy the GenAIIDP solution:

1. [Quick Start with Pre-built Assets](#option-1-deploy-with-pre-built-assets)
2. [Build and Deploy from Source](#option-2-build-deployment-assets-from-source-code)

## Option 1: Deploy with Pre-built Assets

To quickly deploy the GenAI-IDP solution in your own AWS account:

1. Log into the [AWS console](https://console.aws.amazon.com/).
   _Note: If you are logged in as an IAM user, ensure your account has administrator permissions to create and manage the necessary resources and components for this application._
   
2. Choose the **Launch Stack** button below for your desired AWS region to open the AWS CloudFormation console and create a new stack:

| Region name           | Region code | Launch                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US West (Oregon)      | us-west-2   | [![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://s3.us-west-2.amazonaws.com/bobs-artifacts-us-west-2/genaiidp-preview-latest/idp-main.yaml&stackName=IDP) |

3. Review the template parameters and provide values as needed
4. Check the acknowledgment box and click **Create stack**
5. Wait for the stack to reach the `CREATE_COMPLETE` state

## Option 2: Build Deployment Assets from Source Code

### Dependencies

You need to have the following packages installed on your computer:

1. bash shell (Linux, MacOS, Windows-WSL)
2. aws (AWS CLI)
3. [sam (AWS SAM)](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
4. python 3.11 or later
5. A local Docker daemon

Copy the repo to your computer. Either:
- Use the git command to clone the repo, if you have access
- OR, download and expand the ZIP file for the repo, or use the ZIP file that has been shared with you

### Build and Publish the Solution

To build and publish your own template to your own S3 bucket:

* `cfn_bucket_basename`: A prefix added to the beginning of the bucket name (e.g. `idp-1234567890` to ensure global uniqueness) 
* `cfn_prefix`: A prefix added to CloudFormation resources (e.g. `idp` or `idp-dev`)

Navigate into the project root directory and, in a bash shell, run:

```bash
./publish.sh <cfn_bucket_basename> <cfn_prefix> <region e.g. us-east-1>
```

This script:
- Checks your system dependencies for required packages
- Creates CloudFormation templates and asset zip files
- Publishes the templates and required assets to an S3 bucket in your account
- The bucket will be named `<cfn_bucket_basename>-<region>` (created if it doesn't exist)

Example:
```bash
./publish.sh idp-1234567890 idp us-east-1
```

Optional: Add a final parameter `public` if you want to make the published artifacts publicly accessible:
```bash
./publish.sh idp-1234567890 idp us-east-1 public
```
Note: Your bucket and account must be configured not to Block Public Access using new ACLs.

> **Troubleshooting**: 
> * If the process throws an error `Docker daemon is not running` but Docker Desktop or similar is running, it may be necessary to examine the current docker context with the command `docker context ls`. 
> * To set the Docker context daemon, use the `docker context use` command, e.g. `docker context use desktop-linux`
> * Alternatively, set the `DOCKER_HOST` to the socket running the desired Docker daemon, e.g. `export DOCKER_HOST=unix:///Users/username/.docker/run/docker.sock`

When completed, the script displays:
- The CloudFormation template's S3 URL
- A 1-click URL for launching the stack creation in the CloudFormation console

### Deployment Options

#### Recommended: Deploy using AWS CloudFormation console
For your first deployment, use the `1-Click Launch URL` provided by the publish script. This lets you inspect the available parameter options in the console.

#### CLI Deployment
For scripted/automated deployments, use the AWS CLI:

```bash
aws cloudformation deploy \
  --region <region> \
  --template-file <template-file> \
  --s3-bucket <bucket-name> \
  --s3-prefix <s3-prefix> \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides IDPPattern="<pattern-name>" AdminEmail=<your-email> \
  --stack-name <your-stack-name>
```

**Pattern Parameter Options:**
* `Pattern1` - Packet or Media processing with Bedrock Data Automation (BDA)
  * Can use an existing BDA project or create a new demo project
* `Pattern2` - Packet processing with Textract and Bedrock
  * Supports both page-level and holistic classification
  * Recommended for first-time users
* `Pattern3` - Packet processing with Textract, SageMaker(UDOP), and Bedrock
  * Requires a UDOP model in S3 that will be deployed on SageMaker

After deployment, check the Outputs tab in the CloudFormation console to find links to dashboards, buckets, workflows, and other solution resources.

## Testing the Solution

### Basic Test

1. Open the `S3InputBucketConsoleURL` and `S3OutputBucketConsoleURL` from the stack Outputs tab
2. Open the `StateMachineConsoleURL` from the stack Outputs tab
3. Upload a PDF form to the Input bucket (sample files are in the `./samples` folder)
4. Monitor the Step Functions execution to observe the workflow
5. When complete, check the Output bucket for the structured JSON file with extracted fields

### Upload Multiple Sample Files

To copy a sample file multiple times for testing:

```bash
n=10
for i in `seq 1 $n`; do aws s3 cp ./samples/lending_package.pdf s3://idp-inputbucket-kmsxxxxxxxxx/lending_package-$i.pdf; done
```

### Testing Individual Lambda Functions Locally

To test any lambda function locally:

1. Change directory to the folder containing the function's `template.yaml`
2. Create an input event file (some templates are in the `./testing` folder)
3. Verify `./testing/env.json` and change the region if necessary
4. Run `sam build` to package the function(s)
5. Use `sam local` to run the function:
   ```bash
   sam local invoke OCRFunction -e testing/OCRFunction-event.json --env-vars testing/env.json
   ```

### Steady-State Volume Testing

Use the load simulator script to test high document volumes:

```bash
python ./scripts/simulate_load.py -s source_bucket -k prefix/exampledoc.pdf -d idp-kmsxxxxxxxxx -r 500 -t 10
```

This simulates an incoming document rate of 500 docs per minute for 10 minutes.

### Variable Volume Testing

Use the dynamic load simulator script for variable document rates over time:

```bash
python ./scripts/simulate_load.py -s source_bucket -k prefix/exampledoc.pdf -d idp-kmsxxxxxxxxx -f schedule.csv
```

This simulates incoming documents based on minute-by-minute rates in the schedule CSV file.
