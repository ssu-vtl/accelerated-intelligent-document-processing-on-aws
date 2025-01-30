// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React from 'react';
import { useParams } from 'react-router-dom';

import { BreadcrumbGroup } from '@awsui/components-react';

import { DOCUMENTS_PATH } from '../../routes/constants';
import { callListBreadcrumbItems } from '../document-list/breadcrumbs';

const Breadcrumbs = () => {
  const { callId } = useParams();
  const documentDetailsBreadcrumbItems = [
    ...callListBreadcrumbItems,
    { text: callId, href: `#${DOCUMENTS_PATH}/${callId}` },
  ];

  return <BreadcrumbGroup ariaLabel="Breadcrumbs" items={documentDetailsBreadcrumbItems} />;
};

export default Breadcrumbs;
