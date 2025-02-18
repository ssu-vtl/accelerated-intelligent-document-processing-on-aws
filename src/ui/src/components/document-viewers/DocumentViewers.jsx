/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { SpaceBetween, Box, Button } from '@awsui/components-react';
import FileViewer from '../document-viewer/FileViewer';
import EvaluationReportViewer from '../document-viewer/EvaluationReportViewer';

const ViewerControls = ({ onViewSource, onViewReport, isSourceVisible, isReportVisible, evaluationReportUri }) => (
  <div className="flex flex-row gap-4 items-center">
    <Button onClick={onViewSource} variant={isSourceVisible ? 'primary' : 'normal'}>
      {isSourceVisible ? 'Close Source Document' : 'View Source Document'}
    </Button>
    {evaluationReportUri && (
      <Button onClick={onViewReport} variant={isReportVisible ? 'primary' : 'normal'}>
        {isReportVisible ? 'Close Evaluation Report' : 'View Evaluation Report'}
      </Button>
    )}
  </div>
);

const ViewerContent = ({ isSourceVisible, isReportVisible, objectKey, evaluationReportUri }) => {
  if (!isSourceVisible && !isReportVisible) {
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
          <EvaluationReportViewer
            objectKey={objectKey}
            evaluationReportUri={evaluationReportUri}
            showControls={false}
          />
        </div>
      )}
    </div>
  );
};

const DocumentViewers = ({ objectKey, evaluationReportUri }) => {
  const [isSourceVisible, setIsSourceVisible] = useState(false);
  const [isReportVisible, setIsReportVisible] = useState(false);

  const handleViewSource = () => {
    setIsSourceVisible(!isSourceVisible);
  };

  const handleViewReport = () => {
    setIsReportVisible(!isReportVisible);
  };

  return (
    <Box>
      <SpaceBetween size="s">
        <ViewerControls
          onViewSource={handleViewSource}
          onViewReport={handleViewReport}
          isSourceVisible={isSourceVisible}
          isReportVisible={isReportVisible}
          evaluationReportUri={evaluationReportUri}
        />
        <ViewerContent
          isSourceVisible={isSourceVisible}
          isReportVisible={isReportVisible}
          objectKey={objectKey}
          evaluationReportUri={evaluationReportUri}
        />
      </SpaceBetween>
    </Box>
  );
};

export default DocumentViewers;
