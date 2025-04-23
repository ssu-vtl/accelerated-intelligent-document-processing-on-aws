/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { Box } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import DOMPurify from 'dompurify';
import useSettingsContext from '../../contexts/settings';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';
import useAppContext from '../../contexts/app';
import getFileContents from '../../graphql/queries/getFileContents';

const logger = new Logger('FileViewer');

// Helper function to create a safe data URL for HTML content
const createSafeDataUrl = (content, contentType) => {
  // For HTML content, sanitize with DOMPurify
  if (contentType.includes('html')) {
    const sanitizedContent = DOMPurify.sanitize(content, {
      FORBID_TAGS: ['script', 'iframe', 'object', 'embed'],
      FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onmouseout'],
    });
    return `data:${contentType};charset=utf-8,${encodeURIComponent(sanitizedContent)}`;
  }

  // For other text-based content, use as is
  return `data:${contentType};charset=utf-8,${encodeURIComponent(content)}`;
};

const FileViewer = ({ objectKey }) => {
  const [presignedUrl, setPresignedUrl] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [contentType, setContentType] = useState(null);
  const { settings } = useSettingsContext();
  const { currentCredentials } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMethod, setViewMethod] = useState('presigned'); // 'presigned' or 'content'

  // Fetch file contents via GraphQL API for HTML files
  const fetchFileContents = async (s3Url) => {
    try {
      logger.info('Fetching file contents via GraphQL for:', s3Url);
      const response = await API.graphql({
        query: getFileContents,
        variables: { s3Uri: s3Url },
      });

      const result = response.data.getFileContents;
      logger.info('Content type received:', result.contentType);
      logger.info('Binary content?', result.isBinary);

      // Set content and type
      setFileContent(result.content);
      setContentType(result.contentType);

      // Determine view method based on content type and binary flag
      if (result.isBinary === true) {
        // Always use presigned URL for binary content
        setViewMethod('presigned');
      } else if (result.contentType.includes('html') || result.contentType.includes('text/plain')) {
        // Use content-based viewing for HTML and text content
        setViewMethod('content');
      } else {
        // Use presigned URL for other content
        setViewMethod('presigned');
      }

      return result;
    } catch (err) {
      logger.error('Error fetching file contents:', err);
      throw err;
    }
  };

  // Generate presigned URL for direct viewing
  const generateUrl = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (!settings.InputBucket) {
        throw new Error('Input bucket not configured');
      }

      const region = process.env.REACT_APP_AWS_REGION;
      const s3Url = `https://${settings.InputBucket}.s3.${region}.amazonaws.com/${objectKey}`;

      // First fetch the content via GraphQL to determine content type
      await fetchFileContents(s3Url);

      // If we're still using presigned URLs, generate one
      if (viewMethod === 'presigned') {
        logger.info('Generating presigned URL for:', s3Url);
        const url = await generateS3PresignedUrl(s3Url, currentCredentials);
        setPresignedUrl(url);
      }
    } catch (err) {
      logger.error('Error preparing document for viewing:', err);
      setError('Failed to load document. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    generateUrl();
  }, [objectKey]);

  if (error) {
    return (
      <Box color="text-status-error" padding="s">
        {error}
      </Box>
    );
  }

  // Render loading state
  if (isLoading) {
    return (
      <Box textAlign="center" padding="s">
        Loading document...
      </Box>
    );
  }

  // Render content-based viewer (for HTML, etc.)
  if (viewMethod === 'content' && fileContent && contentType) {
    const safeDataUrl = createSafeDataUrl(fileContent, contentType);

    return (
      <Box className="document-container" padding={{ top: 's' }}>
        <iframe
          src={safeDataUrl}
          title="Document Viewer"
          width="100%"
          height="800px"
          className="h-full w-full"
          sandbox="allow-same-origin allow-popups allow-forms"
          referrerPolicy="no-referrer"
        />
      </Box>
    );
  }

  // Render presigned URL viewer (for PDFs, images, etc.)
  if (viewMethod === 'presigned' && presignedUrl) {
    return (
      <Box className="document-container" padding={{ top: 's' }}>
        <iframe
          src={presignedUrl}
          title="Document Viewer"
          width="100%"
          height="800px"
          className="h-full w-full"
          sandbox="allow-same-origin allow-popups allow-forms"
          referrerPolicy="no-referrer"
        />
      </Box>
    );
  }

  // Default fallback
  return (
    <Box textAlign="center" padding="s">
      Unable to display document.
    </Box>
  );
};

export default FileViewer;
