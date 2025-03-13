/* eslint-disable react/no-array-index-key */
/* eslint-disable no-use-before-define */
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  SpaceBetween,
  FormField,
  Input,
  Textarea,
  Toggle,
  Select,
  Button,
  Header,
  Container,
  ColumnLayout,
} from '@awsui/components-react';

// Helper functions outside the component to avoid hoisting issues
const getConstraintText = (property) => {
  const constraints = [];
  if (property.minimum !== undefined) {
    constraints.push(`Min: ${property.minimum}`);
  }
  if (property.maximum !== undefined) {
    constraints.push(`Max: ${property.maximum}`);
  }
  return constraints.join(', ');
};

const FormView = ({ schema, formValues, onChange }) => {
  // Track expanded state for all list items across the form
  const [expandedItems, setExpandedItems] = useState({});
  const getValueAtPath = (obj, path) => {
    const segments = path.split(/[.[\]]+/).filter(Boolean);
    // For debugging
    console.log(`Getting value at path: ${path}`, segments);

    const result = segments.reduce((acc, segment) => {
      if (acc === null || acc === undefined) {
        return undefined;
      }
      return acc[segment];
    }, obj);

    // For debugging
    console.log(`Value at path ${path}:`, result);
    return result;
  };

  const updateValue = (path, value) => {
    const newValues = { ...formValues };
    const segments = path.split(/[.[\]]+/).filter(Boolean);
    let current = newValues;

    segments.slice(0, -1).forEach((segment) => {
      if (!current[segment]) {
        // Initialize arrays for list items
        const nextSegment = segments[segments.indexOf(segment) + 1];
        if (nextSegment && !Number.isNaN(parseInt(nextSegment, 10))) {
          current[segment] = [];
        } else {
          current[segment] = {};
        }
      }
      current = current[segment];
    });

    current[segments[segments.length - 1]] = value;
    onChange(newValues);
  };

  // Define renderField first as a function declaration
  function renderField(key, property, path = '') {
    // Fix for double path issue - when we render a field, we need to determine its path
    // If path is empty, the path is just the key
    // If path exists, we need to append the key to create a full path
    const currentPath = path ? `${path}.${key}` : key;
    console.log(`Determining path for field ${key} with parent path ${path} -> result: ${currentPath}`);
    const value = getValueAtPath(formValues, currentPath);

    if (property.type === 'list') {
      return renderListField(key, property, currentPath);
    }

    if (property.type === 'object') {
      // For object fields, we're passing the path WITHOUT appending the key
      // because renderObjectField will handle that internally
      return renderObjectField(key, property, path);
    }

    return renderInputField(key, property, value, currentPath);
  }

  function renderObjectField(key, property, path) {
    if (!property.properties) {
      return null;
    }

    // Get the full path for this object
    const fullPath = path ? `${path}.${key}` : key;

    // Create a proper section header for top-level objects
    const isTopLevel = !path || path === '';

    // Check if this object should have a special container layout
    // based on the schema definition
    const shouldUseContainer = isTopLevel && property.format === 'section';

    // Get the section title from metadata if available
    const sectionTitle = property.sectionLabel || `${key.charAt(0).toUpperCase() + key.slice(1)} Configuration`;

    // Log the current path and object values for debugging
    const objectValue = getValueAtPath(formValues, fullPath);
    console.log(`Rendering object field: ${key} at fullPath: ${fullPath}`, objectValue);

    return (
      <Box padding="s">
        {shouldUseContainer ? (
          <Container header={<Header variant="h3">{sectionTitle}</Header>}>
            <SpaceBetween size="s">
              {Object.entries(property.properties).map(([propKey, propSchema]) => {
                // Pass the full path to renderField for each property
                return <Box key={propKey}>{renderField(propKey, propSchema, fullPath)}</Box>;
              })}
            </SpaceBetween>
          </Container>
        ) : (
          <SpaceBetween size="xs">
            {/* No nested object title for more compact layout */}
            {Object.entries(property.properties).map(([propKey, propSchema]) => {
              // Pass the full path to renderField for each property
              return <Box key={propKey}>{renderField(propKey, propSchema, fullPath)}</Box>;
            })}
          </SpaceBetween>
        )}
      </Box>
    );
  }

  function renderListField(key, property, path) {
    const values = getValueAtPath(formValues, path) || [];

    // Get list item display settings from schema metadata
    const columnCount = property.columns ? parseInt(property.columns, 10) : 2;

    // Calculate nesting level for indentation
    const nestLevel = property.nestLevel || 0;
    const nextNestLevel = nestLevel + 1;

    // Get list descriptions and labels
    const listDescription = property.description || '';
    const itemLabel = property.itemLabel || key.charAt(0).toUpperCase() + key.slice(1).replace(/s$/, '');

    // Container settings
    const useContainer = property.containerFormat === 'section';
    const sectionTitle = property.sectionLabel || `${key.charAt(0).toUpperCase() + key.slice(1)}`;

    // Create unique keys for this list
    const listKey = `list:${path}`;

    // Toggle expansion of list
    const toggleListExpand = () => {
      setExpandedItems((prev) => ({
        ...prev,
        [listKey]: !prev[listKey],
      }));
    };

    // Check if list is expanded - default to collapsed
    const isListExpanded = expandedItems[listKey] === true;

    // List header with expand/collapse control
    const listHeader = (
      <Box
        display="flex"
        alignItems="center"
        padding={{ left: `${nestLevel * 8}px`, top: 'xs', bottom: 'xs' }}
        borderBottom="divider-light"
        backgroundColor="background-paper-default"
        borderRadius="xs"
      >
        <Button
          variant="icon"
          iconName={isListExpanded ? 'caret-down-filled' : 'caret-right-filled'}
          onClick={toggleListExpand}
          ariaLabel={isListExpanded ? 'Collapse list' : 'Expand list'}
        />
        <Box fontWeight="bold" fontSize="body-m" margin={{ left: 'xs' }}>
          {listDescription || key.charAt(0).toUpperCase() + key.slice(1)}
        </Box>
      </Box>
    );

    // List content with items - only shown when expanded
    const itemsContent = isListExpanded && (
      <Box padding={{ left: `${nestLevel * 8 + 16}px` }}>
        <SpaceBetween size="xxxs">
          {values.length === 0 && (
            <Box fontStyle="italic" color="text-body-secondary" padding="xs">
              No items added yet
            </Box>
          )}

          {values.map((item, index) => {
            const itemPath = `${path}[${index}]`;

            return (
              <Box key={`${itemPath}-${index}`} borderBottom="divider-light" padding={{ bottom: 'xxxs' }}>
                {/* Item row with number and delete button */}
                <Box display="flex" alignItems="flex-start" padding={{ top: 'xxxs', bottom: 'xxxs' }}>
                  {/* Item number on left margin */}
                  <Box fontWeight="bold" width="24px" textAlign="left" marginRight="xs">
                    {index + 1}.
                  </Box>

                  {/* Content area with property fields and nested lists */}
                  <Box flex="1">
                    {property.items.type === 'object' ? (
                      <ColumnLayout columns={columnCount} variant="text-grid">
                        {Object.entries(property.items.properties || {}).map(([propKey, propSchema]) => {
                          const propPath = `${itemPath}.${propKey}`;
                          const propValue = getValueAtPath(formValues, propPath);

                          if (propSchema.type === 'list') {
                            // Configure nested list with proper indentation
                            const nestedListProps = {
                              ...propSchema,
                              nestLevel: nextNestLevel,
                            };

                            return (
                              <Box key={propKey} padding={{ top: 'xxxs', bottom: 'xxxs' }} width="100%">
                                {renderListField(propKey, nestedListProps, propPath)}
                              </Box>
                            );
                          }

                          return (
                            <Box key={propKey} padding="xs">
                              {renderInputField(propKey, propSchema, propValue, propPath)}
                            </Box>
                          );
                        })}
                      </ColumnLayout>
                    ) : (
                      // Simple list item (non-object)
                      <Box padding="xs">
                        {renderInputField(`${key}[${index}]`, property.items, values[index], itemPath)}
                      </Box>
                    )}
                  </Box>

                  {/* Delete button */}
                  <Button
                    variant="icon"
                    iconName="remove"
                    onClick={() => {
                      const newValues = [...values];
                      newValues.splice(index, 1);
                      updateValue(path, newValues);
                    }}
                    ariaLabel="Remove item"
                  />
                </Box>
              </Box>
            );
          })}

          {/* Add new item button */}
          <Box>
            <Button
              iconName="add-plus"
              onClick={() => {
                // Create a new empty item
                let newValue;
                if (property.items.type === 'object') {
                  newValue = {};
                  if (property.items.properties) {
                    Object.entries(property.items.properties).forEach(([propKey, propSchema]) => {
                      if (propSchema.type === 'list') {
                        newValue[propKey] = [];
                      } else if (propSchema.type === 'object') {
                        newValue[propKey] = {};
                      } else {
                        newValue[propKey] = '';
                      }
                    });
                  }
                } else {
                  newValue = '';
                }

                // Add new item
                updateValue(path, [...values, newValue]);
              }}
            >
              Add {itemLabel}
            </Button>
          </Box>
        </SpaceBetween>
      </Box>
    );

    // Combine header and content
    const fullListContent = (
      <Box>
        {listHeader}
        {itemsContent}
      </Box>
    );

    // Render with or without container
    if (useContainer) {
      return (
        <Container header={<Header variant="h3">{sectionTitle}</Header>}>
          <Box padding="s">{fullListContent}</Box>
        </Container>
      );
    }

    return <Box>{fullListContent}</Box>;
  }

  function renderInputField(key, property, value, path) {
    let input;

    if (property.enum) {
      input = (
        <Select
          selectedOption={{ value: value || '', label: value || '' }}
          onChange={({ detail }) => updateValue(path, detail.selectedOption.value)}
          options={property.enum.map((opt) => ({ value: opt, label: opt }))}
        />
      );
    } else if (property.format === 'text-area' || path.toLowerCase().includes('prompt')) {
      input = <Textarea value={value || ''} onChange={({ detail }) => updateValue(path, detail.value)} rows={5} />;
    } else if (property.type === 'boolean') {
      input = <Toggle checked={!!value} onChange={({ detail }) => updateValue(path, detail.checked)} />;
    } else {
      input = (
        <Input
          value={value !== undefined && value !== null ? String(value) : ''}
          type={property.type === 'number' ? 'number' : 'text'}
          onChange={({ detail }) => {
            let finalValue = detail.value;
            if (property.type === 'number' && detail.value !== '') {
              finalValue = Number(detail.value);
            }
            updateValue(path, finalValue);
          }}
        />
      );
    }

    // More compact layout - just show description as the label
    const displayText = property.description || key;
    const constraints = getConstraintText(property);

    return (
      <FormField label={displayText} constraintText={constraints.length > 0 ? constraints : undefined}>
        {input}
      </FormField>
    );
  }

  // Create a sorted list of properties based on their order attribute
  const getSortedProperties = () => {
    const entries = Object.entries(schema?.properties || {});

    // Add an order property if not present (default to 999)
    const withOrder = entries.map(([key, prop]) => ({
      key,
      property: prop,
      order: prop.order ? parseInt(prop.order, 10) : 999,
    }));

    // Sort by order
    return withOrder.sort((a, b) => a.order - b.order);
  };

  return (
    <Box style={{ height: '70vh', overflow: 'auto' }} padding="s">
      <SpaceBetween size="l">
        {getSortedProperties().map(({ key, property }) => (
          <Box key={key}>{renderField(key, property)}</Box>
        ))}
      </SpaceBetween>
    </Box>
  );
};

FormView.propTypes = {
  schema: PropTypes.shape({
    properties: PropTypes.objectOf(
      PropTypes.shape({
        type: PropTypes.string,
        description: PropTypes.string,
      }),
    ),
  }),
  formValues: PropTypes.shape({}),
  onChange: PropTypes.func.isRequired,
};

FormView.defaultProps = {
  schema: { properties: {} },
  formValues: {},
};

export default FormView;
