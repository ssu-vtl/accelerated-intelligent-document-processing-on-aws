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

const DocumentDetails = () => {
  const { documentId } = useParams();
  const { documents, getDocumentDetailsFromIds, setToolsOpen } = useDocumentsContext();
  const { settings } = useSettingsContext();

  const [document, setCall] = useState(null);

  useEffect(async () => {
    if (!documentId || !document || !documents?.length) {
      return;
    }
    const documentsFiltered = documents.filter((c) => c.ObjectKey === documentId);
    if (documentsFiltered && documentsFiltered?.length) {
      const documentsMap = mapDocumentsAttributes([documentsFiltered[0]], settings);
      const documentDetails = documentsMap[0];
      if (documentDetails?.updatedAt && document.updatedAt < documentDetails.updatedAt) {
        logger.debug('Updating document', documentDetails);
        setCall(documentDetails);
      }
    }
  }, [documents, documentId]);

  return (
    document && (
      <CallPanel item={document} setToolsOpen={setToolsOpen} getDocumentDetailsFromIds={getDocumentDetailsFromIds} />
    )
  );
};

export default DocumentDetails;
