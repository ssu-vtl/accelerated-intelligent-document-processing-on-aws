// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Logger } from 'aws-amplify';

import useDocumentsContext from '../../contexts/documents';
import useSettingsContext from '../../contexts/settings';

import mapDocumentsAttributes from '../common/map-document-attributes';

import '@awsui/global-styles/index.css';

import CallPanel from '../call-panel';

const logger = new Logger('documentDetails');

const documentDetails = () => {
  const { callId } = useParams();
  const { calls, getDocumentDetailsFromIds, setToolsOpen } = useDocumentsContext();
  const { settings } = useSettingsContext();

  const [call, setCall] = useState(null);

  useEffect(async () => {
    if (!callId || !call || !calls?.length) {
      return;
    }
    const callsFiltered = calls.filter((c) => c.CallId === callId);
    if (callsFiltered && callsFiltered?.length) {
      const callsMap = mapDocumentsAttributes([callsFiltered[0]], settings);
      const documentDetails = callsMap[0];
      if (documentDetails?.updatedAt && call.updatedAt < documentDetails.updatedAt) {
        logger.debug('Updating call', documentDetails);
        setCall(documentDetails);
      }
    }
  }, [calls, callId]);

  return (
    call && <CallPanel item={call} setToolsOpen={setToolsOpen} getDocumentDetailsFromIds={getDocumentDetailsFromIds} />
  );
};

export default documentDetails;
