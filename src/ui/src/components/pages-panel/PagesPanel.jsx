/* eslint-disable react/prop-types */
import React from 'react';
import { Box, Container, SpaceBetween, Table } from '@awsui/components-react';
import FileViewer from '../file-viewer/FileViewer';

// Cell renderer components
const IdCell = ({ item }) => <span>{item.Id}</span>;
const ClassCell = ({ item }) => <span>{item.Class || '-'}</span>;
const ThumbnailCell = ({ item }) => (
  <div style={{ width: '100px', height: '100px' }}>
    {item.ImageUri ? (
      <img
        src={item.ImageUri}
        alt="Page thumbnail"
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          objectFit: 'contain',
        }}
        title="Page thumbnail"
      />
    ) : (
      <Box textAlign="center" color="inherit">
        No image
      </Box>
    )}
  </div>
);

const ActionsCell = ({ item }) =>
  item.TextUri ? (
    <FileViewer fileUri={item.TextUri} fileType="json" buttonText="View JSON" />
  ) : (
    <Box color="text-status-inactive">No text available</Box>
  );

// Column definitions
const COLUMN_DEFINITIONS = [
  {
    id: 'id',
    header: 'Page ID',
    cell: (item) => <IdCell item={item} />,
    sortingField: 'Id',
  },
  {
    id: 'class',
    header: 'Class/Type',
    cell: (item) => <ClassCell item={item} />,
    sortingField: 'Class',
  },
  {
    id: 'thumbnail',
    header: 'Thumbnail',
    cell: (item) => <ThumbnailCell item={item} />,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item) => <ActionsCell item={item} />,
  },
];

const PagesPanel = ({ pages }) => {
  return (
    <SpaceBetween size="l">
      <Container header={<h2>Document Pages</h2>}>
        <Table
          columnDefinitions={COLUMN_DEFINITIONS}
          items={pages || []}
          sortingDisabled
          variant="embedded"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No pages</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                This document has no pages.
              </Box>
            </Box>
          }
        />
      </Container>
    </SpaceBetween>
  );
};

export default PagesPanel;
