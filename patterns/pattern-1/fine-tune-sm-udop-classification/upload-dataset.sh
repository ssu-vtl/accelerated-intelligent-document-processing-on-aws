#!/bin/bash

usage() {
    echo "Usage: $0 --zip-file ZIP_FILE --bucket BUCKET [--bucket-prefix PREFIX]"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --zip-file) ZIP_FILE="$2"; shift ;;
        --bucket) BUCKET_NAME="$2"; shift ;;
        --bucket-prefix) S3_PREFIX="$2"; shift ;;
        *) usage ;;
    esac
    shift
done

if [ -z "$ZIP_FILE" ] || [ -z "$BUCKET_NAME" ]; then
    usage
fi

S3_PREFIX="${S3_PREFIX:-""}"

if [ ! -f "$ZIP_FILE" ]; then
    echo "Error: Zip file '$ZIP_FILE' not found"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
    echo "Bucket '$BUCKET_NAME' does not exist. Creating bucket..."
    if ! aws s3 mb "s3://$BUCKET_NAME"; then
        echo "Error: Failed to create bucket '$BUCKET_NAME'"
        exit 1
    fi
    echo "Bucket created successfully"
fi

TEMP_DIR=$(mktemp -d)
if [ ! -d "$TEMP_DIR" ]; then
    echo "Error: Failed to create temporary directory"
    exit 1
fi

cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "Unzipping files to temporary directory..."
if ! unzip -q "$ZIP_FILE" -d "$TEMP_DIR"; then
    echo "Error: Failed to unzip file"
    exit 1
fi

echo "Uploading files to S3..."
if ! aws s3 sync "$TEMP_DIR" "s3://$BUCKET_NAME/$S3_PREFIX"; then
    echo "Error: Failed to upload files to S3"
    exit 1
fi

echo "Upload completed successfully"
echo "Files uploaded to: s3://$BUCKET_NAME/$S3_PREFIX"