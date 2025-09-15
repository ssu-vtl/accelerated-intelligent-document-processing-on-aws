// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { Box, StatusIndicator, SpaceBetween } from '@awsui/components-react';
import PropTypes from 'prop-types';
import useSettingsContext from '../../contexts/settings';

const KnowledgeBaseStatus = ({ showDetails = true }) => {
  const { settings } = useSettingsContext();

  // Determine knowledge base configuration
  const parseBool = (v) => (typeof v === 'boolean' ? v : v === 'true');
  const isOpenSearchEnabled = parseBool(settings?.ShouldUseDocumentKnowledgeBase);
  const isS3VectorsEnabled = parseBool(settings?.ShouldUseS3VectorsKnowledgeBase);
  const isKnowledgeBaseEnabled = isOpenSearchEnabled || isS3VectorsEnabled;

  let status = 'stopped';
  let statusText = 'Disabled';
  let backendType = 'None';
  let description = 'Document Knowledge Base is not enabled for this deployment.';

  if (isKnowledgeBaseEnabled) {
    status = 'success';
    statusText = 'Active';
    if (isS3VectorsEnabled) {
      backendType = 'S3 Vectors';
      description = `Using S3 Vectors backend for cost-effective large-scale document 
        processing. Query response times: 2-10 seconds.`;
    } else {
      backendType = 'OpenSearch (Bedrock KB)';
      description = 'Using OpenSearch backend via Bedrock Knowledge Base for fast query responses and analytics.';
    }
  }

  if (!showDetails) {
    return (
      <Box>
        <StatusIndicator type={status}>Knowledge Base: {backendType}</StatusIndicator>
      </Box>
    );
  }

  return (
    <Box>
      <SpaceBetween size="xs">
        <Box>
          <StatusIndicator type={status}>
            <strong>Knowledge Base Status:</strong> {statusText}
          </StatusIndicator>
        </Box>
        <Box>
          <strong>Backend Type:</strong> {backendType}
        </Box>
        <Box variant="small">{description}</Box>
      </SpaceBetween>
    </Box>
  );
};

KnowledgeBaseStatus.propTypes = {
  showDetails: PropTypes.bool,
};

KnowledgeBaseStatus.defaultProps = {
  showDetails: true,
};

export default KnowledgeBaseStatus;
