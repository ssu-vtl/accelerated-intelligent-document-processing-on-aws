/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { SpaceBetween, Box, Button, StatusIndicator } from '@awsui/components-react';
import { API, graphqlOperation, Logger } from 'aws-amplify';
import copyToBaselineMutation from '../../graphql/queries/copyToBaseline';
import FileViewer from '../document-viewer/FileViewer';
import MarkdownReportViewer from '../document-viewer/MarkdownReportViewer';

const logger = new Logger('DocumentViewers');

const ViewerControls = ({
  onViewSource,
  onViewReport,
  onViewSummary,
  onSetAsBaseline,
  isSourceVisible,
  isReportVisible,
  isSummaryVisible,
  evaluationReportUri,
  summaryReportUri,
  copyStatus,
}) => (
  <SpaceBetween direction="horizontal" size="xs">
    <Button onClick={onViewSource} variant={isSourceVisible ? 'primary' : 'normal'}>
      {isSourceVisible ? 'Close Source Document' : 'View Source Document'}
    </Button>
    {evaluationReportUri && (
      <Button onClick={onViewReport} variant={isReportVisible ? 'primary' : 'normal'}>
        {isReportVisible ? 'Close Evaluation Report' : 'View Evaluation Report'}
      </Button>
    )}
    {summaryReportUri && (
      <Button onClick={onViewSummary} variant={isSummaryVisible ? 'primary' : 'normal'}>
        {isSummaryVisible ? 'Close Document Summary' : 'View Document Summary'}
      </Button>
    )}
    <Button onClick={onSetAsBaseline} disabled={copyStatus === 'in-progress'}>
      Use as Evaluation Baseline
    </Button>
    {copyStatus === 'in-progress' && <StatusIndicator type="in-progress">Copying...</StatusIndicator>}
    {copyStatus === 'success' && <StatusIndicator type="success">Copy successful</StatusIndicator>}
    {copyStatus === 'error' && <StatusIndicator type="error">Copy failed</StatusIndicator>}
  </SpaceBetween>
);

const ViewerContent = ({
  isSourceVisible,
  isReportVisible,
  isSummaryVisible,
  objectKey,
  evaluationReportUri,
  summaryReportUri,
}) => {
  if (!isSourceVisible && !isReportVisible && !isSummaryVisible) {
    return null;
  }

  return (
    <div className="flex flex-col lg:flex-row gap-4 mt-4">
      {isSourceVisible && (
        <div className="flex-1 min-w-0">
          <FileViewer objectKey={objectKey} showControls={false} />
        </div>
      )}
      {isReportVisible && (
        <div className="flex-1 min-w-0">
          <MarkdownReportViewer
            reportUri={evaluationReportUri}
            documentId={objectKey}
            title="Evaluation Report"
            emptyMessage="Evaluation report not available for this document"
          />
        </div>
      )}
      {isSummaryVisible && (
        <div className="flex-1 min-w-0">
          <MarkdownReportViewer
            reportUri={summaryReportUri}
            documentId={objectKey}
            title="Document Summary"
            emptyMessage="Summary report not available for this document"
          />
        </div>
      )}
    </div>
  );
};

const DocumentViewers = ({ objectKey, evaluationReportUri, summaryReportUri }) => {
  const [isSourceVisible, setIsSourceVisible] = useState(false);
  const [isReportVisible, setIsReportVisible] = useState(false);
  const [isSummaryVisible, setIsSummaryVisible] = useState(false);
  const [copyStatus, setCopyStatus] = useState(null);

  const handleViewSource = () => {
    setIsSourceVisible(!isSourceVisible);
  };

  const handleViewReport = () => {
    setIsReportVisible(!isReportVisible);
  };

  const handleViewSummary = () => {
    setIsSummaryVisible(!isSummaryVisible);
  };

  const handleSetAsBaseline = async () => {
    setCopyStatus('in-progress');
    try {
      const result = await API.graphql(
        graphqlOperation(copyToBaselineMutation, {
          objectKey,
        }),
      );

      if (result.data.copyToBaseline.success) {
        setCopyStatus('success');
        setTimeout(() => setCopyStatus(null), 3000);
      } else {
        setCopyStatus('error');
        logger.error('Failed to copy:', result.data.copyToBaseline.message);
      }
    } catch (error) {
      setCopyStatus('error');
      logger.error('Error copying to evaluation baseline:', error);
    }
  };

  return (
    <Box>
      <SpaceBetween size="s">
        <ViewerControls
          onViewSource={handleViewSource}
          onViewReport={handleViewReport}
          onViewSummary={handleViewSummary}
          onSetAsBaseline={handleSetAsBaseline}
          isSourceVisible={isSourceVisible}
          isReportVisible={isReportVisible}
          isSummaryVisible={isSummaryVisible}
          evaluationReportUri={evaluationReportUri}
          summaryReportUri={summaryReportUri}
          copyStatus={copyStatus}
        />
        <ViewerContent
          isSourceVisible={isSourceVisible}
          isReportVisible={isReportVisible}
          isSummaryVisible={isSummaryVisible}
          objectKey={objectKey}
          evaluationReportUri={evaluationReportUri}
          summaryReportUri={summaryReportUri}
        />
      </SpaceBetween>
    </Box>
  );
};

export default DocumentViewers;
