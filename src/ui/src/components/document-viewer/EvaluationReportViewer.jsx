/* eslint-disable react/prop-types */
import React, { useState, useEffect } from 'react';
import { Box } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import getFileContents from '../../graphql/queries/getFileContents';
import './EvaluationReportViewer.css';

const logger = new Logger('EvaluationReportViewer');

const MarkdownViewer = ({ content }) => (
  <Box className="markdown-viewer">
    <div className="table-container">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
        {content}
      </ReactMarkdown>
    </div>
  </Box>
);

const EvaluationReportViewer = ({ evaluationReportUri }) => {
  const [reportContent, setReportContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!evaluationReportUri) return;

      setIsLoading(true);
      setError(null);
      try {
        logger.info('Fetching evaluation report:', evaluationReportUri);

        const response = await API.graphql({
          query: getFileContents,
          variables: { s3Uri: evaluationReportUri },
        });

        const content = response.data.getFileContents;
        logger.debug('Received report content:', `${content.substring(0, 100)}...`);

        setReportContent(content);
      } catch (err) {
        logger.error('Error fetching evaluation report:', err);
        setError('Failed to load evaluation report. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [evaluationReportUri]);

  if (!evaluationReportUri) {
    return (
      <Box color="text-status-inactive" padding={{ top: 's' }}>
        Evaluation report not available for this document
      </Box>
    );
  }

  if (error) {
    return (
      <Box color="text-status-error" padding="s">
        {error}
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box textAlign="center" padding="s">
        Loading evaluation report...
      </Box>
    );
  }

  return reportContent && <MarkdownViewer content={reportContent} />;
};

export default EvaluationReportViewer;
