/* eslint-disable react/prop-types */
import React from 'react';
import { Box, ColumnLayout, Container, SpaceBetween, Button, Header, Table } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import './DocumentPanel.css';
import DocumentViewers from '../document-viewers/DocumentViewers';
import SectionsPanel from '../sections-panel';
import PagesPanel from '../pages-panel';

const logger = new Logger('DocumentPanel');

// Component to display metering information in a table
const MeteringTable = ({ meteringData }) => {
  if (!meteringData) {
    return null;
  }

  // Transform metering data into table rows
  const tableItems = [];
  Object.entries(meteringData).forEach(([service, serviceData]) => {
    Object.entries(serviceData).forEach(([api, apiData]) => {
      Object.entries(apiData).forEach(([unit, value]) => {
        tableItems.push({
          service,
          api,
          unit,
          value: String(value),
        });
      });
    });
  });

  return (
    <Table
      columnDefinitions={[
        { id: 'service', header: 'Service', cell: (item) => item.service },
        { id: 'api', header: 'API', cell: (item) => item.api },
        { id: 'unit', header: 'Unit', cell: (item) => item.unit },
        { id: 'value', header: 'Value', cell: (item) => item.value },
      ]}
      items={tableItems}
      loadingText="Loading resources"
      sortingDisabled
      empty={
        <Box textAlign="center" color="inherit">
          <b>No metering data</b>
          <Box padding={{ bottom: 's' }} variant="p" color="inherit">
            No metering data is available for this document.
          </Box>
        </Box>
      }
    />
  );
};

const DocumentAttributes = ({ item }) => {
  return (
    <Container>
      <ColumnLayout columns={6} variant="text-grid">
        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Document ID</strong>
            </Box>
            <div>{item.objectKey}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Status</strong>
            </Box>
            <div>{item.objectStatus}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Submitted</strong>
            </Box>
            <div>{item.initialEventTime}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Completed</strong>
            </Box>
            <div>{item.completionTime}</div>
          </div>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Duration</strong>
            </Box>
            <div>{item.duration}</div>
          </div>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  );
};

export const DocumentPanel = ({ item, setToolsOpen, getDocumentDetailsFromIds, onDelete }) => {
  logger.debug('DocumentPanel item', item);

  return (
    <SpaceBetween size="s">
      <Container
        header={
          <Header
            variant="h2"
            actions={
              onDelete && (
                <Button iconName="remove" variant="normal" onClick={onDelete}>
                  Delete
                </Button>
              )
            }
          >
            Document Details
          </Header>
        }
      >
        <SpaceBetween size="l">
          <DocumentAttributes
            item={item}
            setToolsOpen={setToolsOpen}
            getDocumentDetailsFromIds={getDocumentDetailsFromIds}
          />

          {item.metering && (
            <div>
              <Box margin={{ top: 'l', bottom: 'm' }}>
                <Header variant="h3">Metering</Header>
              </Box>
              <MeteringTable meteringData={item.metering} />
            </div>
          )}
        </SpaceBetween>
      </Container>
      <DocumentViewers objectKey={item.objectKey} evaluationReportUri={item.evaluationReportUri} />
      <SectionsPanel sections={item.sections} />
      <PagesPanel pages={item.pages} />
    </SpaceBetween>
  );
};

export default DocumentPanel;
