/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { Box, SpaceBetween, Button } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import useSettingsContext from '../../contexts/settings';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';
import useAppContext from '../../contexts/app';

const logger = new Logger('FileViewer');

const FileViewer = ({ objectKey }) => {
  const [presignedUrl, setPresignedUrl] = useState(null);
  const { settings } = useSettingsContext();
  const { currentCredentials } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateUrl = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (!settings.InputBucket) {
        throw new Error('Input bucket not configured');
      }
      const region = process.env.REACT_APP_AWS_REGION;
      logger.info('Generating presigned URL for bucket, key, region:', settings.InputBucket, objectKey, region);
      const s3Url = `https://${settings.InputBucket}.s3.${region}.amazonaws.com/${objectKey}`;
      logger.info('Generating presigned URL for:', s3Url);
      const url = await generateS3PresignedUrl(s3Url, currentCredentials);
      setPresignedUrl(url);
    } catch (err) {
      logger.error('Error generating presigned URL:', err);
      setError('Failed to load document. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const closeViewer = () => {
    setPresignedUrl(null);
  };

  return (
    <Box>
      {!presignedUrl && (
        <Button onClick={generateUrl} loading={isLoading} disabled={isLoading}>
          View Source Document
        </Button>
      )}

      {error && (
        <Box color="text-status-error" padding="s">
          {error}
        </Box>
      )}

      {presignedUrl && (
        <SpaceBetween size="s">
          <Button onClick={closeViewer}>Close Viewer</Button>
          <Box className="pdf-container" padding={{ top: 's' }}>
            <iframe src={presignedUrl} title="Document Viewer" width="100%" height="800px" className="h-full w-full" />
          </Box>
        </SpaceBetween>
      )}
    </Box>
  );
};

export default FileViewer;
