// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { React } from 'react';
import { Route, Switch, useLocation } from 'react-router-dom';
import { SideNavigation } from '@awsui/components-react';

import { DOCUMENTS_PATH, DOCUMENTS_KB_QUERY_PATH, DEFAULT_PATH } from '../../routes/constants';

export const callsNavHeader = { text: 'GenAIDP', href: `#${DEFAULT_PATH}` };
export const callsNavItems = [
  { type: 'link', text: 'Document List', href: `#${DOCUMENTS_PATH}` },
  { type: 'link', text: 'Document KB (coming)', href: `#${DOCUMENTS_KB_QUERY_PATH}` },
  {
    type: 'section',
    text: 'Resources',
    items: [
      {
        type: 'link',
        text: 'README',
        href: 'https://gitlab.aws.dev/genaiic-reusable-assets/engagement-artifacts/genaiic-idp-accelerator/-/blob/main/README.md',
        external: true,
      },
      {
        type: 'link',
        text: 'Source Code',
        href: 'https://gitlab.aws.dev/genaiic-reusable-assets/engagement-artifacts/genaiic-idp-accelerator',
        external: true,
      },
    ],
  },
];

const defaultOnFollowHandler = (ev) => {
  // XXX keep the locked href for our demo pages
  // ev.preventDefault();
  console.log(ev);
};

/* eslint-disable react/prop-types */
const Navigation = ({ header = callsNavHeader, items = callsNavItems, onFollowHandler = defaultOnFollowHandler }) => {
  const location = useLocation();
  const path = location.pathname;
  let activeHref = `#${DEFAULT_PATH}`;
  if (path.includes(DOCUMENTS_KB_QUERY_PATH)) {
    activeHref = `#${DOCUMENTS_KB_QUERY_PATH}`;
  } else if (path.includes(DOCUMENTS_PATH)) {
    activeHref = `#${DOCUMENTS_PATH}`;
  }
  return (
    <Switch>
      <Route path={DOCUMENTS_PATH}>
        <SideNavigation
          items={items || callsNavItems}
          header={header || callsNavHeader}
          activeHref={activeHref}
          onFollow={onFollowHandler}
        />
      </Route>
    </Switch>
  );
};

export default Navigation;
