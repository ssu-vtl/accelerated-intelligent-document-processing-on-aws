/* eslint-disable react/prop-types */
import React, { useState, useEffect } from 'react';
import { Box, ColumnLayout, Container, SpaceBetween, Button, Header, Table } from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import './DocumentPanel.css';
import DocumentViewers from '../document-viewers/DocumentViewers';
import SectionsPanel from '../sections-panel';
import PagesPanel from '../pages-panel';
import useConfiguration from '../../hooks/use-configuration';

const logger = new Logger('DocumentPanel');

// Format the cost cell content based on whether it's a total row
const formatCostCell = (item) => {
  if (item.isTotal) {
    return <Box fontWeight="bold">{`${item.note}: ${item.cost}`}</Box>;
  }
  return item.cost;
};

// Component to display metering information in a table
const MeteringTable = ({ meteringData, documentItem }) => {
  // Use configuration to get pricing data
  const { mergedConfig, loading } = useConfiguration();
  const [pricingData, setPricingData] = useState({});
  // We no longer use a default unit cost, showing "None" instead

  useEffect(() => {
    if (mergedConfig && mergedConfig.pricing) {
      // Convert pricing array to lookup object for easier access
      const pricingLookup = {};
      mergedConfig.pricing.forEach((item) => {
        if (item.name && item.units) {
          pricingLookup[item.name] = {};
          item.units.forEach((unitItem) => {
            if (unitItem.name && unitItem.price !== undefined) {
              // Ensure price is stored as a number
              pricingLookup[item.name][unitItem.name] = Number(unitItem.price);
            }
          });
        }
      });
      setPricingData(pricingLookup);
      logger.debug('Pricing data initialized:', pricingLookup);
    }
  }, [mergedConfig]);

  if (!meteringData) {
    return null;
  }

  if (loading) {
    return <Box>Loading pricing data...</Box>;
  }

  // Transform metering data into table rows
  const tableItems = [];
  let totalCost = 0;

  Object.entries(meteringData).forEach(([serviceApi, metrics]) => {
    Object.entries(metrics).forEach(([unit, value]) => {
      const numericValue = Number(value);

      // Look up the unit price from the pricing data
      let unitPrice = null;
      let unitPriceDisplayValue = 'None';
      let cost = 0;
      if (pricingData[serviceApi] && pricingData[serviceApi][unit] !== undefined) {
        unitPrice = Number(pricingData[serviceApi][unit]);
        if (!Number.isNaN(unitPrice)) {
          unitPriceDisplayValue = `$${unitPrice}`;
          cost = numericValue * unitPrice;
          totalCost += cost;
          logger.debug(`Found price for ${serviceApi}/${unit}: ${unitPriceDisplayValue}`);
        } else {
          logger.warn(`Invalid price for ${serviceApi}/${unit}, using None`);
        }
      } else {
        logger.debug(`No price found for ${serviceApi}/${unit}, using None`);
      }

      tableItems.push({
        serviceApi,
        unit,
        value: String(numericValue),
        unitCost: unitPriceDisplayValue,
        cost: unitPrice !== null ? `$${cost.toFixed(4)}` : 'N/A',
        isTotal: false,
      });
    });
  });

  // Get page count from the document
  const numPages = (documentItem && documentItem.pageCount) || 1;
  const costPerPage = totalCost / numPages;

  // Add total rows
  tableItems.push({
    serviceApi: '',
    unit: '',
    value: '',
    unitCost: '',
    cost: `$${totalCost.toFixed(4)}`,
    isTotal: true,
    note: 'Total',
  });

  tableItems.push({
    serviceApi: '',
    unit: '',
    value: '',
    unitCost: '',
    cost: `$${costPerPage.toFixed(4)}`,
    isTotal: true,
    note: 'Per Page',
  });

  return (
    <Table
      columnDefinitions={[
        {
          id: 'serviceApi',
          header: 'Service/Api',
          cell: (rowItem) => rowItem.serviceApi,
        },
        {
          id: 'unit',
          header: 'Unit',
          cell: (rowItem) => rowItem.unit,
        },
        {
          id: 'value',
          header: 'Value',
          cell: (rowItem) => rowItem.value,
        },
        {
          id: 'unitCost',
          header: 'Unit Cost',
          cell: (rowItem) => rowItem.unitCost,
        },
        {
          id: 'cost',
          header: 'Estimated Cost',
          cell: formatCostCell,
        },
      ]}
      items={tableItems}
      loadingText="Loading resources"
      sortingDisabled
      wrapLines
      stripedRows
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

        <SpaceBetween size="xs">
          <div>
            <Box margin={{ bottom: 'xxxs' }} color="text-label">
              <strong>Page Count</strong>
            </Box>
            <div>{item.pageCount || 0}</div>
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
              <div style={{ maxWidth: '50%' }}>
                <MeteringTable meteringData={item.metering} documentItem={item} />
              </div>
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
