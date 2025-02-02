// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';
import { Logger } from 'aws-amplify';

import DocumentsQueryLayout from '../components/document-kb-query-layout';
import GenAIDPTopNavigation from '../components/genai-idp-top-navigation';

const logger = new Logger('DocumentsQueryRoutes');

const DocumentsQueryRoutes = () => {
  const { path } = useRouteMatch();
  logger.info('path ', path);

  return (
    <Switch>
      <Route path={path}>
        <div>
          <GenAIDPTopNavigation />
          <DocumentsQueryLayout />
        </div>
      </Route>
    </Switch>
  );
};

export default DocumentsQueryRoutes;
