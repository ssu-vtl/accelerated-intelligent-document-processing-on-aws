// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Logger } from 'aws-amplify';

import useDocumentsContext from '../../contexts/documents';
import useSettingsContext from '../../contexts/settings';

import mapDocumentsAttributes from '../common/map-document-attributes';

import '@awsui/global-styles/index.css';

import DocumentPanel from '../document-panel';

const logger = new Logger('documentDetails');

const DocumentDetails = () => {
  const params = useParams();
  let { objectKey } = params;
  logger.debug('XXX objectKey', objectKey);
  objectKey = decodeURIComponent(objectKey);
  logger.debug('XXX Decoded DocumentDetails', objectKey);

  const { documents, getDocumentDetailsFromIds, setToolsOpen } = useDocumentsContext();
  const { settings } = useSettingsContext();

  const [document, setDocument] = useState(null);

  const sendInitDocumentRequests = async () => {
    const response = await getDocumentDetailsFromIds([objectKey]);
    logger.debug('document detail response', response);
    const documentsMap = mapDocumentsAttributes(response, settings);
    const documentDetails = documentsMap[0];
    if (documentDetails) {
      setDocument(documentDetails);
    }
  };

  useEffect(() => {
    if (!objectKey) {
      return () => {};
    }
    sendInitDocumentRequests();
    return () => {};
  }, [objectKey]);

  useEffect(async () => {
    if (!objectKey || !document || !documents?.length) {
      return;
    }
    const documentsFiltered = documents.filter((c) => c.ObjectKey === objectKey);
    if (documentsFiltered && documentsFiltered?.length) {
      const documentsMap = mapDocumentsAttributes([documentsFiltered[0]], settings);
      const documentDetails = documentsMap[0];
      if (documentDetails?.updatedAt && document.updatedAt < documentDetails.updatedAt) {
        logger.debug('Updating document', documentDetails);
        setDocument(documentDetails);
      }
    }
  }, [documents, objectKey]);

  logger.debug('useEffect for documentDetails', objectKey, document, documents);

  return (
    document && (
      <DocumentPanel
        item={document}
        setToolsOpen={setToolsOpen}
        getDocumentDetailsFromIds={getDocumentDetailsFromIds}
      />
    )
  );
};

export default DocumentDetails;
