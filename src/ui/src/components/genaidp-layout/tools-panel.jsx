// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';

import DocumentListToolsPanel from '../document-list/tools-panel';
import DocumentDetailsToolsPanel from '../document-details/tools-panel';

const ToolsPanel = () => {
  const { path } = useRouteMatch();

  return (
    <Switch>
      <Route exact path={path}>
        <DocumentListToolsPanel />
      </Route>
      <Route path={`${path}/:documentId`}>
        <DocumentDetailsToolsPanel />
      </Route>
    </Switch>
  );
};

export default ToolsPanel;
