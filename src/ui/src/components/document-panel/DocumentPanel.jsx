/* eslint-disable react/prop-types */
import React from 'react';
import { Box, ColumnLayout, Container, SpaceBetween } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import './DocumentPanel.css';
import FileViewer from '../file-viewer/FileViewer';
import SectionsPanel from '../sections-panel';
import PagesPanel from '../pages-panel';

const logger = new Logger('DocumentPanel');

const DocumentAttributes = ({ item }) => {
  return (
    <Container>
      <ColumnLayout columns={6} variant="text-grid">
        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Document ID</strong>
            </Box>
            <div>{item.objectKey}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Submitted</strong>
            </Box>
            <div>{item.initialEventTime}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Completed</strong>
            </Box>
            <div>{item.completionTime}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Duration</strong>
            </Box>
            <div>{item.duration}</div>
          </div>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  );
};

export const DocumentPanel = ({ item, setToolsOpen, getDocumentDetailsFromIds }) => {
  logger.debug('DocumentPanel item', item);
  return (
    <SpaceBetween size="s">
      <DocumentAttributes
        item={item}
        setToolsOpen={setToolsOpen}
        getDocumentDetailsFromIds={getDocumentDetailsFromIds}
      />
      <FileViewer objectKey={item.objectKey} />
      <SectionsPanel sections={item.sections} />
      <PagesPanel pages={item.pages} />
    </SpaceBetween>
  );
};

export default DocumentPanel;
