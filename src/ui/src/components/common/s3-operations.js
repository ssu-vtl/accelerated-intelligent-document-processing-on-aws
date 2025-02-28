// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { S3Client, CopyObjectCommand } from '@aws-sdk/client-s3';
import { Logger } from 'aws-amplify';

const logger = new Logger('s3-operations');

const copyToEvaluationBaseline = async (credentials, region, sourceBucket, objectKey, destinationBucket) => {
  try {
    const s3Client = new S3Client({
      region,
      credentials: {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      },
    });

    await s3Client.send(
      new CopyObjectCommand({
        CopySource: `${sourceBucket}/${objectKey}`,
        Bucket: destinationBucket,
        Key: objectKey,
      }),
    );

    return { success: true };
  } catch (error) {
    logger.error('Failed to copy to evaluation baseline:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

export default copyToEvaluationBaseline;
