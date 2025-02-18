/* eslint-disable react/prop-types */
import React from 'react';
import { Box, Container, SpaceBetween, Table } from '@awsui/components-react';
import FileViewer from '../document-viewer/JSONViewer';

// Cell renderer components
const IdCell = ({ item }) => <span>{item.Id}</span>;
const ClassCell = ({ item }) => <span>{item.Class}</span>;
const PageIdsCell = ({ item }) => <span>{item.PageIds.join(', ')}</span>;
const ActionsCell = ({ item }) => <FileViewer fileUri={item.OutputJSONUri} fileType="json" buttonText="View JSON" />;

// Column definitions
const COLUMN_DEFINITIONS = [
  {
    id: 'id',
    header: 'Section ID',
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
    id: 'pageIds',
    header: 'Page IDs',
    cell: (item) => <PageIdsCell item={item} />,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item) => <ActionsCell item={item} />,
  },
];

const SectionsPanel = ({ sections }) => {
  // Create column definitions
  const columnDefinitions = COLUMN_DEFINITIONS.map((column) => ({
    ...column,
    cell: (item) => column.cell(item),
  }));

  return (
    <SpaceBetween size="l">
      <Container header={<h2>Document Sections</h2>}>
        <Table
          columnDefinitions={columnDefinitions}
          items={sections || []}
          sortingDisabled
          variant="embedded"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No sections</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                This document has no sections.
              </Box>
            </Box>
          }
        />
      </Container>
    </SpaceBetween>
  );
};

export default SectionsPanel;
