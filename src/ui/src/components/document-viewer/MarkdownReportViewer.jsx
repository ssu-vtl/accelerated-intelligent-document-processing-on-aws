/* eslint-disable react/prop-types */
import React, { useState, useEffect, useRef } from 'react';
import { Box, Button, SpaceBetween } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import getFileContents from '../../graphql/queries/getFileContents';
import './MarkdownReportViewer.css';

const logger = new Logger('MarkdownReportViewer');

const MarkdownViewer = ({ content, documentName, title }) => {
  const contentRef = useRef(null);

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>${title || 'Report'} - ${documentName || 'Document'}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            table { border-collapse: collapse; margin: 16px 0; width: auto; }
            th, td { border: 1px solid #ddd; padding: 8px 12px; }
            th { background-color: #f1f1f1; font-weight: bold; text-align: left; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            h1 { font-size: 24px; margin-bottom: 16px; }
            h2 { font-size: 20px; margin-bottom: 12px; margin-top: 24px; }
            h3 { font-size: 18px; margin-bottom: 8px; margin-top: 16px; }
          </style>
        </head>
        <body>
          <div>${contentRef.current?.innerHTML || ''}</div>
        </body>
      </html>
    `;

    printWindow.document.open();
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  const handleDownload = () => {
    // Create a blob from the markdown content
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    // Create a temporary link element
    const a = document.createElement('a');
    a.href = url;
    a.download = `${documentName || title.toLowerCase().replace(/\s+/g, '-') || 'report'}.md`;

    // Append, click, and remove
    document.body.appendChild(a);
    a.click();

    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box className="markdown-viewer">
      <div className="tools-container">
        <SpaceBetween direction="horizontal" size="xs">
          <Button variant="normal" onClick={handleDownload} iconName="download" iconAlign="left" formAction="none">
            Download
          </Button>
          <Button variant="normal" onClick={handlePrint} iconAlign="left" formAction="none">
            Print
          </Button>
        </SpaceBetween>
      </div>

      <div className="table-container" ref={contentRef}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
          {content}
        </ReactMarkdown>
      </div>
    </Box>
  );
};

const MarkdownReportViewer = ({ reportUri, documentId, title = 'Report', emptyMessage }) => {
  const [reportContent, setReportContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!reportUri) return;

      setIsLoading(true);
      setError(null);
      try {
        logger.info(`Fetching ${title}:`, reportUri);

        const response = await API.graphql({
          query: getFileContents,
          variables: { s3Uri: reportUri },
        });

        const content = response.data.getFileContents;
        logger.debug(`Received ${title} content:`, `${content.substring(0, 100)}...`);

        setReportContent(content);
      } catch (err) {
        logger.error(`Error fetching ${title}:`, err);
        setError(`Failed to load ${title.toLowerCase()}. Please try again.`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [reportUri, title]);

  if (!reportUri) {
    return (
      <Box color="text-status-inactive" padding={{ top: 's' }}>
        {emptyMessage || `${title} not available for this document`}
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
        Loading {title.toLowerCase()}...
      </Box>
    );
  }

  return (
    reportContent && <MarkdownViewer content={reportContent} documentName={documentId || 'document'} title={title} />
  );
};

export default MarkdownReportViewer;
