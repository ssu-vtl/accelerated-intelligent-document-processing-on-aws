// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import React from 'react';
import { Button, ButtonDropdown, CollectionPreferences, Link, SpaceBetween } from '@awsui/components-react';

import { TableHeader } from '../common/table';
import { DOCUMENTS_PATH } from '../../routes/constants';
import { shareModal, deleteModal } from '../common/meeting-controls';

export const KEY_COLUMN_ID = 'object_key';

export const COLUMN_DEFINITIONS_MAIN = [
  {
    id: KEY_COLUMN_ID,
    header: 'Document ID',
    cell: (item) => <Link href={`#${DOCUMENTS_PATH}/${item.object_key}`}>{item.object_key}</Link>,
    sortingField: 'object_key',
    width: 325,
  },
  {
    id: 'initial_event_time',
    header: 'Submission Timestamp',
    cell: (item) => item.initial_event_time,
    sortingField: 'initial_event_time',
    isDescending: false,
  },
  {
    id: 'completion_time',
    header: 'Completion Timestamp',
    cell: (item) => item.completion_time,
    sortingField: 'completion_time',
    width: 225,
  },
  {
    id: 'status',
    header: 'Status',
    cell: (item) => item.status,
    sortingField: 'status',
    width: 150,
  },
  {
    id: 'workflow_duration',
    header: 'Duration',
    cell: () => 'TODO',
    sortingField: 'workflow_duration',
  },
];

export const DEFAULT_SORT_COLUMN = COLUMN_DEFINITIONS_MAIN[3];

export const SELECTION_LABELS = {
  itemSelectionLabel: (data, row) => `select ${row.callId}`,
  allItemsSelectionLabel: () => 'select all',
  selectionGroupLabel: 'Meeting selection',
};

const PAGE_SIZE_OPTIONS = [
  { value: 10, label: '10 Documents' },
  { value: 30, label: '30 Documents' },
  { value: 50, label: '50 Documents' },
];

const VISIBLE_CONTENT_OPTIONS = [
  {
    label: 'Meeting list properties',
    options: [
      { id: 'object_key', label: 'Document ID', editable: false },
      { id: 'initial_event_time', label: 'Submission Timestamp' },
      { id: 'completion_time', label: 'Completion Timestamp' },
      { id: 'status', label: 'Status' },
      { id: 'workflow_duration', label: 'Duration' },
    ],
  },
];

const VISIBLE_CONTENT = ['object_key', 'initial_event_time', 'completion_time', 'status', 'workflow_duration'];

export const DEFAULT_PREFERENCES = {
  pageSize: PAGE_SIZE_OPTIONS[0].value,
  visibleContent: VISIBLE_CONTENT,
  wraplines: false,
};

/* eslint-disable react/prop-types, react/jsx-props-no-spreading */
export const DocumentsPreferences = ({
  preferences,
  setPreferences,
  disabled,
  pageSizeOptions = PAGE_SIZE_OPTIONS,
  visibleContentOptions = VISIBLE_CONTENT_OPTIONS,
}) => (
  <CollectionPreferences
    title="Preferences"
    confirmLabel="Confirm"
    cancelLabel="Cancel"
    disabled={disabled}
    preferences={preferences}
    onConfirm={({ detail }) => setPreferences(detail)}
    pageSizePreference={{
      title: 'Page size',
      options: pageSizeOptions,
    }}
    wrapLinesPreference={{
      label: 'Wrap lines',
      description: 'Check to see all the text and wrap the lines',
    }}
    visibleContentPreference={{
      title: 'Select visible columns',
      options: visibleContentOptions,
    }}
  />
);

// number of shards per day used by the list calls API
export const DOCUMENT_LIST_SHARDS_PER_DAY = 6;
const TIME_PERIOD_DROPDOWN_CONFIG = {
  'refresh-2h': { count: 0.5, text: '2 hrs' },
  'refresh-4h': { count: 1, text: '4 hrs' },
  'refresh-8h': { count: DOCUMENT_LIST_SHARDS_PER_DAY / 3, text: '8 hrs' },
  'refresh-1d': { count: DOCUMENT_LIST_SHARDS_PER_DAY, text: '1 day' },
  'refresh-2d': { count: 2 * DOCUMENT_LIST_SHARDS_PER_DAY, text: '2 days' },
  'refresh-1w': { count: 7 * DOCUMENT_LIST_SHARDS_PER_DAY, text: '1 week' },
  'refresh-2w': { count: 14 * DOCUMENT_LIST_SHARDS_PER_DAY, text: '2 weeks' },
  'refresh-1m': { count: 30 * DOCUMENT_LIST_SHARDS_PER_DAY, text: '30 days' },
};
const TIME_PERIOD_DROPDOWN_ITEMS = Object.keys(TIME_PERIOD_DROPDOWN_CONFIG).map((k) => ({
  id: k,
  ...TIME_PERIOD_DROPDOWN_CONFIG[k],
}));

// local storage key to persist the last periods to load
export const PERIODS_TO_LOAD_STORAGE_KEY = 'periodsToLoad';

export const DocumentsCommonHeader = ({ resourceName = 'Documents', ...props }) => {
  const onPeriodToLoadChange = ({ detail }) => {
    const { id } = detail;
    const shardCount = TIME_PERIOD_DROPDOWN_CONFIG[id].count;
    props.setPeriodsToLoad(shardCount);
    localStorage.setItem(PERIODS_TO_LOAD_STORAGE_KEY, JSON.stringify(shardCount));
  };

  // eslint-disable-next-line
  const periodText =
    TIME_PERIOD_DROPDOWN_ITEMS.filter((i) => i.count === props.periodsToLoad)[0]?.text || '';

  return (
    <TableHeader
      title={resourceName}
      actionButtons={
        <SpaceBetween size="xxs" direction="horizontal">
          <ButtonDropdown loading={props.loading} onItemClick={onPeriodToLoadChange} items={TIME_PERIOD_DROPDOWN_ITEMS}>
            {`Load: ${periodText}`}
          </ButtonDropdown>
          <Button
            iconName="refresh"
            variant="normal"
            loading={props.loading}
            onClick={() => props.setIsLoading(true)}
          />
          <Button
            iconName="download"
            variant="normal"
            loading={props.loading}
            onClick={() => props.downloadToExcel()}
          />
          {shareModal(props)}
          {deleteModal(props)}
        </SpaceBetween>
      }
      {...props}
    />
  );
};
