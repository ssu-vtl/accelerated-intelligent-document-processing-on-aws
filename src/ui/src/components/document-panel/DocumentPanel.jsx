// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { Box, ColumnLayout, Container, SpaceBetween } from '@awsui/components-react';

import './DocumentPanel.css';

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
              <strong>Completion Timestamp</strong>
            </Box>
            <div>{item.initiationTimeStamp}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Last Update Timestamp</strong>
            </Box>
            <div>{item.updatedAt}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Duration</strong>
            </Box>
            <div>{item.conversationDurationTimeStamp}</div>
          </div>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  );
};

export const DocumentPanel = ({ item, setToolsOpen, getDocumentDetailsFromIds }) => {
  return (
    <SpaceBetween size="s">
      <DocumentAttributes
        item={item}
        setToolsOpen={setToolsOpen}
        getDocumentDetailsFromIds={getDocumentDetailsFromIds}
      />
    </SpaceBetween>
  );
};

export default DocumentPanel;
