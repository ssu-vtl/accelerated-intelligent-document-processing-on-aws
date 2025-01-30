// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import gql from 'graphql-tag';

export default gql`
  query Query($object_key: ID!) {
    getDocument(object_key: $object_key) {
      object_key
      status: String
      initial_event_time
      queued_time
      workflow_start_time
      completion_time
      execution_arn
      workflow_status
      expires_after
    }
  }
`;
