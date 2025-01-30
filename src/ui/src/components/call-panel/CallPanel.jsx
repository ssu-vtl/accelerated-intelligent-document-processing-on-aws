// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import { Box, Button, ColumnLayout, Container, SpaceBetween, StatusIndicator } from '@awsui/components-react';

import './CallPanel.css';

/* eslint-disable react/prop-types, react/destructuring-assignment */
const CallAttributes = ({ item }) => {
  return (
    <Container>
      <ColumnLayout columns={6} variant="text-grid">
        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Document ID</strong>
            </Box>
            <div>{item.callId}</div>
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

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Status</strong>
            </Box>
            <StatusIndicator type={item.recordingStatusIcon}>{` ${item.recordingStatusLabel} `}</StatusIndicator>
          </div>
        </SpaceBetween>
        {item?.pcaUrl?.length && (
          <SpaceBetween size="xs">
            <div>
              <Box margin={{ bottom: 'xxxs' }} color="text-label">
                <strong>Post Document Processing</strong>
              </Box>
              <Button variant="normal" href={item.pcaUrl} target="_blank" iconAlign="right" iconName="external">
                Open in Post Call Analytics
              </Button>
            </div>
          </SpaceBetween>
        )}
      </ColumnLayout>
    </Container>
  );
};

export const CallPanel = ({ item, setToolsOpen, getDocumentDetailsFromIds }) => {
  return (
    <SpaceBetween size="s">
      <CallAttributes item={item} setToolsOpen={setToolsOpen} getDocumentDetailsFromIds={getDocumentDetailsFromIds} />
    </SpaceBetween>
  );
};

export default CallPanel;
