/* eslint-disable react/prop-types */
import React, { useState } from 'react';
import { Box, Button, Container, SpaceBetween, Table } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import useAppContext from '../../contexts/app';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';

const logger = new Logger('PagesPanel');

// Separate component for the ViewTextButton
const ViewTextButton = ({ page, onView, isLoading, selectedPageId }) => (
  <Button onClick={() => onView(page)} loading={isLoading && selectedPageId === page.Id}>
    View Text
  </Button>
);

// Cell renderer components
const IdCell = ({ item }) => <span>{item.Id}</span>;
const ClassCell = ({ item }) => <span>{item.Class || '-'}</span>;
const ThumbnailCell = ({ imageUrl }) => (
  <div style={{ width: '100px', height: '100px' }}>
    {imageUrl ? (
      <a href={imageUrl} target="_blank" rel="noopener noreferrer" style={{ cursor: 'pointer' }}>
        <img
          src={imageUrl}
          alt="Page thumbnail"
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            transition: 'transform 0.2s',
            ':hover': {
              transform: 'scale(1.05)',
            },
          }}
          title="Click to view full size image"
        />
      </a>
    ) : (
      <Box textAlign="center" color="inherit">
        No image
      </Box>
    )}
  </div>
);

const ActionsCell = ({ item, onView, isLoading, selectedPageId }) =>
  item.TextUri ? (
    <ViewTextButton page={item} onView={onView} isLoading={isLoading} selectedPageId={selectedPageId} />
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
    cell: (item, { thumbnailUrls }) => <ThumbnailCell imageUrl={thumbnailUrls[item.Id]} />,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item, { onView, isLoading, selectedPageId }) => (
      <ActionsCell item={item} onView={onView} isLoading={isLoading} selectedPageId={selectedPageId} />
    ),
  },
];

const PagesPanel = ({ pages }) => {
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [textUrl, setTextUrl] = useState(null);
  const [thumbnailUrls, setThumbnailUrls] = useState({});
  const { currentCredentials } = useAppContext();

  const loadThumbnails = async () => {
    if (!pages) return;

    const urls = {};
    await Promise.all(
      pages.map(async (page) => {
        if (page.ImageUri) {
          try {
            const url = await generateS3PresignedUrl(page.ImageUri, currentCredentials);
            urls[page.Id] = url;
          } catch (err) {
            logger.error('Error generating presigned URL for thumbnail:', err);
            urls[page.Id] = null;
          }
        }
      }),
    );
    setThumbnailUrls(urls);
  };

  React.useEffect(() => {
    loadThumbnails();
  }, [pages]);

  const handleViewText = async (page) => {
    setIsLoading(true);
    setSelectedPageId(page.Id);
    try {
      const url = await generateS3PresignedUrl(page.TextUri, currentCredentials);
      setTextUrl(url);
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
        onView: handleViewText,
        isLoading,
        selectedPageId,
        thumbnailUrls,
      }),
  }));

  return (
    <SpaceBetween size="l">
      <Container header={<h2>Document Pages</h2>}>
        <Table
          columnDefinitions={columnDefinitions}
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

      {textUrl && (
        <Container
          header={
            <SpaceBetween size="m" direction="horizontal">
              <h3>Page {selectedPageId} Text Content</h3>
              <Button
                onClick={() => {
                  setTextUrl(null);
                  setSelectedPageId(null);
                }}
              >
                Close
              </Button>
            </SpaceBetween>
          }
        >
          <iframe
            src={textUrl}
            title="Text Viewer"
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

export default PagesPanel;
