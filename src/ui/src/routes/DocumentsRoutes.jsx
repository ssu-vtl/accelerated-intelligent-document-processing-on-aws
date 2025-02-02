// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';
import { Logger } from 'aws-amplify';

import GenAIDPLayout from '../components/genaidp-layout';
import GenAIDPTopNavigation from '../components/genai-idp-top-navigation';

const logger = new Logger('DocumentsRoutes');

const DocumentsRoutes = () => {
  const { path } = useRouteMatch();
  logger.info('path ', path);

  return (
    <Switch>
      <Route path={path}>
        <div>
          <GenAIDPTopNavigation />
          <GenAIDPLayout />
        </div>
      </Route>
    </Switch>
  );
};

export default DocumentsRoutes;
