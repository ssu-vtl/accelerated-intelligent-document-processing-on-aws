/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { Box, Button, Container, SpaceBetween, Table } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import useAppContext from '../../contexts/app';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';

const logger = new Logger('SectionsPanel');

// Separate component for the ViewJsonButton
const ViewJsonButton = ({ section, onView, isLoading, selectedSectionId }) => (
  <Button onClick={() => onView(section)} loading={isLoading && selectedSectionId === section.Id}>
    View JSON
  </Button>
);

// Separate component for the cell renderers
const IdCell = ({ item }) => <span>{item.Id}</span>;
const ClassCell = ({ item }) => <span>{item.Class}</span>;
const PageIdsCell = ({ item }) => <span>{item.PageIds.join(', ')}</span>;
const ActionsCell = ({ item, onView, isLoading, selectedSectionId }) => (
  <ViewJsonButton section={item} onView={onView} isLoading={isLoading} selectedSectionId={selectedSectionId} />
);

// Column definitions moved outside component
const COLUMN_DEFINITIONS = [
  {
    id: 'id',
    header: 'Section ID',
    cell: (item) => <IdCell item={item} />,
    sortingField: 'Id',
  },
  {
    id: 'class',
    header: 'Document Class',
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
    cell: (item, { onView, isLoading, selectedSectionId }) => (
      <ActionsCell item={item} onView={onView} isLoading={isLoading} selectedSectionId={selectedSectionId} />
    ),
  },
];

const SectionsPanel = ({ sections }) => {
  const [selectedSectionId, setSelectedSectionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [jsonUrl, setJsonUrl] = useState(null);
  const { currentCredentials } = useAppContext();

  const handleViewJson = async (section) => {
    setIsLoading(true);
    setSelectedSectionId(section.Id);
    try {
      const s3Url = section.OutputJSONUri;

      logger.info('Generating presigned URL for:', s3Url);

      // Use the existing generateS3PresignedUrl utility
      const url = await generateS3PresignedUrl(s3Url, currentCredentials);
      setJsonUrl(url);
    } catch (err) {
      logger.error('Error generating presigned URL:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Create column definitions with necessary context
  const columnDefinitions = COLUMN_DEFINITIONS.map((column) => ({
    ...column,
    cell: (item) =>
      column.cell(item, {
        onView: handleViewJson,
        isLoading,
        selectedSectionId,
      }),
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

      {jsonUrl && (
        <Container
          header={
            <SpaceBetween size="m" direction="horizontal">
              <h3>Section {selectedSectionId} JSON Content</h3>
              <Button
                onClick={() => {
                  setJsonUrl(null);
                  setSelectedSectionId(null);
                }}
              >
                Close
              </Button>
            </SpaceBetween>
          }
        >
          <iframe
            src={jsonUrl}
            title="JSON Viewer"
            width="100%"
            height="400px"
            style={{
              border: '1px solid #eaeded',
              borderRadius: '4px',
            }}
          />
        </Container>
      )}
    </SpaceBetween>
  );
};

export default SectionsPanel;
