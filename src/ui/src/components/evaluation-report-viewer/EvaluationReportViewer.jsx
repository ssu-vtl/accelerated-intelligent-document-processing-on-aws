/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { Box, SpaceBetween, Button } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import useAppContext from '../../contexts/app';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';

const logger = new Logger('EvaluationReportViewer');

const EvaluationReportViewer = ({ evaluationReportUri }) => {
  const [presignedUrl, setPresignedUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { currentCredentials } = useAppContext();

  const generateUrl = async () => {
    setIsLoading(true);
    setError(null);
    try {
      logger.info('Generating presigned URL for:', evaluationReportUri);
      const url = await generateS3PresignedUrl(evaluationReportUri, currentCredentials);
      setPresignedUrl(url);
    } catch (err) {
      logger.error('Error generating presigned URL:', err);
      setError('Failed to load evaluation report. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const closeViewer = () => {
    setPresignedUrl(null);
  };

  if (!evaluationReportUri) {
    return (
      <Box color="text-status-inactive" padding={{ top: 's' }}>
        Evaluation report not available for this document
      </Box>
    );
  }

  return (
    <Box className="w-full">
      {!presignedUrl && (
        <Button onClick={generateUrl} loading={isLoading} disabled={isLoading}>
          View Evaluation Report
        </Button>
      )}

      {error && (
        <Box color="text-status-error" padding="s">
          {error}
        </Box>
      )}

      {presignedUrl && (
        <SpaceBetween size="s">
          <Button onClick={closeViewer}>Close Report</Button>
          <Box className="w-full">
            <iframe
              src={presignedUrl}
              title="Evaluation Report Viewer"
              width="100%"
              height="800px"
              className="border border-solid border-gray-200 rounded-md w-full"
            />
          </Box>
        </SpaceBetween>
      )}
    </Box>
  );
};

export default EvaluationReportViewer;
