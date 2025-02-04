// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { Box, ColumnLayout, Container, SpaceBetween } from '@awsui/components-react';

import './DocumentPanel.css';
import { Logger } from 'aws-amplify';
import FileViewer from '../file-viewer/FileViewer';

const logger = new Logger('DocumentPanel');

/* eslint-disable react/prop-types, react/destructuring-assignment */
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
    </SpaceBetween>
  );
};

export default DocumentPanel;
