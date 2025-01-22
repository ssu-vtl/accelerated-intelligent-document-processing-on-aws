#!/bin/bash
##############################################################################################
# Create new Cfn artifacts bucket if not already existing
# Build artifacts
# Upload artifacts to S3 bucket for deployment with CloudFormation
##############################################################################################

# Stop the publish process on failures
set -e

USAGE="$0 <cfn_bucket_basename> <cfn_prefix> <region> [public]"

if ! [ -x "$(command -v sam)" ]; then
  echo 'Error: sam is not installed and required.' >&2
  echo 'Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html' >&2
  exit 1
fi
sam_version=$(sam --version | awk '{print $4}')
min_sam_version="1.118.0"
if [[ $(echo -e "$min_sam_version\n$sam_version" | sort -V | tail -n1) == $min_sam_version && $min_sam_version != $sam_version ]]; then
    echo "Error: sam version >= $min_sam_version is not installed and required. (Installed version is $sam_version)" >&2
    echo 'Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/manage-sam-cli-versions.html' >&2
    exit 1
fi

BUCKET_BASENAME=$1
[ -z "$BUCKET_BASENAME" ] && echo "Cfn bucket name is a required parameter. Usage $USAGE" && exit 1

PREFIX=$2
[ -z "$PREFIX" ] && echo "Prefix is a required parameter. Usage $USAGE" && exit 1

REGION=$3
[ -z "$REGION" ] && echo "Region is a required parameter. Usage $USAGE" && exit 1
export AWS_DEFAULT_REGION=$REGION

ACL=$4
if [ "$ACL" == "public" ]; then
  echo "Published S3 artifacts will be acessible by public (read-only)"
  PUBLIC=true
else
  echo "Published S3 artifacts will NOT be acessible by public."
  PUBLIC=false
fi

# Remove trailing slash from prefix if needed, and append VERSION
VERSION=$(cat ./VERSION)
[[ "${PREFIX}" == */ ]] && PREFIX="${PREFIX%?}"
PREFIX_AND_VERSION=${PREFIX}/${VERSION}

# Append region to bucket basename
BUCKET=${BUCKET_BASENAME}-${REGION}

# Create bucket if it doesn't already exist
if [ -x $(aws s3api list-buckets --query 'Buckets[].Name' | grep "\"$BUCKET\"") ]; then
  echo "Creating s3 bucket: $BUCKET"
  aws s3 mb s3://${BUCKET} || exit 1
  aws s3api put-bucket-versioning --bucket ${BUCKET} --versioning-configuration Status=Enabled || exit 1
else
  echo "Using existing bucket: $BUCKET"
fi


# Package and publish the artifacts
is_x86_64() {
  [[ $(uname -m) == "x86_64" ]]
}
if is_x86_64; then
  USE_CONTAINER_FLAG=""
else
  echo "Run SAM build with container on Mac..."
  USE_CONTAINER_FLAG="--use-container "
fi

for nested in patterns/*; do
  echo "Building nested template artifacts in $nested" 
  pushd $nested
  sam build $USE_CONTAINER_FLAG --template-file template.yaml
  sam package \
    --template-file .aws-sam/build/template.yaml \
    --output-template-file .aws-sam/packaged.yaml \
    --s3-bucket ${BUCKET} \
    --s3-prefix ${PREFIX_AND_VERSION}
  popd
done
# build main template
MAIN_TEMPLATE=idp-main.yaml
sam build $USE_CONTAINER_FLAG --template-file template.yaml
sam package \
 --template-file .aws-sam/build/template.yaml \
 --output-template-file .aws-sam/${MAIN_TEMPLATE} \
 --s3-bucket ${BUCKET} \
 --s3-prefix ${PREFIX_AND_VERSION}

# upload main template
aws s3 cp .aws-sam/${MAIN_TEMPLATE} s3://${BUCKET}/${PREFIX}/${MAIN_TEMPLATE} || exit 1
TEMPLATE_URL="https://s3.${REGION}.amazonaws.com/${BUCKET}/${PREFIX}/${MAIN_TEMPLATE}"
echo "Validating template: $TEMPLATE_URL"
aws cloudformation validate-template --template-url $TEMPLATE_URL > /dev/null || exit 1

if $PUBLIC; then
echo "Setting public read ACLs on published artifacts"
files=$(aws s3api list-objects --bucket ${BUCKET} --prefix ${PREFIX_AND_VERSION} --query "(Contents)[].[Key]" --output text)
c=$(echo $files | wc -w)
counter=0
for file in $files
  do
  aws s3api put-object-acl --acl public-read --bucket ${BUCKET} --key $file
  counter=$((counter + 1))
  echo -ne "Progress: $counter/$c files processed\r"
  done
aws s3api put-object-acl --acl public-read --bucket ${BUCKET} --key ${PREFIX}/${MAIN_TEMPLATE}
echo ""
echo "Done."
fi

echo "OUTPUTS"
echo Template URL: $TEMPLATE_URL
echo CF Launch URL: https://${REGION}.console.aws.amazon.com/cloudformation/home?region=${REGION}#/stacks/create/review?templateURL=${TEMPLATE_URL}\&stackName=IDP
echo CLI Deploy: aws cloudformation deploy --region $REGION --template-file .aws-sam/${MAIN_TEMPLATE} --s3-bucket ${BUCKET} --s3-prefix ${PREFIX_AND_VERSION} --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides UDOPModelArtifactPath="s3://bucket-name/path/to/model.tar.gz" "<other params>" --stack-name "<your-stack-name>"
echo Done
exit 0

