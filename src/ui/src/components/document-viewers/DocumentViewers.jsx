/* eslint-disable react/prop-types */
import React from 'react';
import { SpaceBetween, Box } from '@awsui/components-react';
import FileViewer from '../file-viewer/FileViewer';
import EvaluationReportViewer from '../evaluation-report-viewer/EvaluationReportViewer';

const DocumentViewers = ({ objectKey, evaluationReportUri }) => {
  return (
    <Box>
      <div className="flex flex-wrap gap-4">
        <div className="w-full">
          <SpaceBetween size="s">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 min-w-0">
                <FileViewer objectKey={objectKey} />
              </div>
              <div className="flex-1 min-w-0">
                <EvaluationReportViewer objectKey={objectKey} evaluationReportUri={evaluationReportUri} />
              </div>
            </div>
          </SpaceBetween>
        </div>
      </div>
    </Box>
  );
};

export default DocumentViewers;
