/* eslint-disable react/no-array-index-key */
/* eslint-disable no-use-before-define */
import React, { useState, useRef, useEffect } from 'react';
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

// Resizable Columns Component
const ResizableColumns = ({ columns, children, columnSpacing = '8px' }) => {
  const [columnWidths, setColumnWidths] = useState([]);
  const containerRef = useRef(null);
  const resizingRef = useRef(null);

  // Initialize column widths
  useEffect(() => {
    if (containerRef.current) {
      // Initialize with equal width columns
      const initialWidth = `${100 / columns}%`;
      setColumnWidths(Array(columns).fill(initialWidth));
    }
  }, [columns]);

  // Start resizing
  const startResize = (index, e) => {
    e.preventDefault();
    resizingRef.current = {
      index,
      startX: e.clientX,
      initialWidths: [...columnWidths],
    };

    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
  };

  // Handle resize
  const handleResize = (e) => {
    if (!resizingRef.current || !containerRef.current) return;

    const { index, startX, initialWidths } = resizingRef.current;
    const containerWidth = containerRef.current.offsetWidth;
    const deltaPixels = e.clientX - startX;
    const deltaPercent = (deltaPixels / containerWidth) * 100;

    // Calculate new widths
    const newWidths = [...initialWidths];
    newWidths[index] = `calc(${initialWidths[index]} + ${deltaPercent}%)`;
    if (index + 1 < columns) {
      newWidths[index + 1] = `calc(${initialWidths[index + 1]} - ${deltaPercent}%)`;
    }

    setColumnWidths(newWidths);
  };

  // Stop resizing
  const stopResize = () => {
    resizingRef.current = null;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  };

  // Create column containers with proper distribution
  const columnElements = [];

  // Prepare to distribute children into columns - properly group elements
  const childrenArray = React.Children.toArray(children);

  // Calculate how many items should go in each column
  const itemsPerColumn = Math.ceil(childrenArray.length / columns);

  // Create columns with their children
  for (let i = 0; i < columns; i += 1) {
    // Calculate which children go in this column
    const startIndex = i * itemsPerColumn;
    const endIndex = Math.min(startIndex + itemsPerColumn, childrenArray.length);
    const columnChildren = childrenArray.slice(startIndex, endIndex);

    // Only create columns that have children or are the first column
    columnElements.push(
      <Box
        key={i}
        style={{
          width: columnWidths[i] || `${100 / columns}%`,
          padding: `0 ${columnSpacing}`,
          transition: 'none',
          position: 'relative',
        }}
      >
        {columnChildren}

        {i < columns - 1 && (
          <Box
            style={{
              position: 'absolute',
              right: '0',
              top: '0',
              width: '8px',
              height: '100%',
              cursor: 'col-resize',
              zIndex: 1,
              touchAction: 'none',
            }}
            onMouseDown={(e) => startResize(i, e)}
          >
            <Box
              style={{
                position: 'absolute',
                right: '3px',
                top: '0',
                width: '2px',
                height: '100%',
                backgroundColor: 'var(--color-border-divider-default, #e9ebed)',
              }}
            />
            {/* Visual indicator on hover */}
            <Box
              style={{
                position: 'absolute',
                right: '3px',
                top: '50%',
                marginTop: '-10px',
                width: '4px',
                height: '20px',
                backgroundColor: 'var(--color-border-control-default, #aab7b8)',
                borderRadius: '2px',
                opacity: 0,
                transition: 'opacity 0.2s',
              }}
              className="resize-handle-indicator"
            />
          </Box>
        )}
      </Box>,
    );
  }

  return (
    <div ref={containerRef} style={{ display: 'flex', width: '100%', position: 'relative' }}>
      {columnElements}
      <style>
        {`
          .resize-handle-indicator {
            opacity: 0;
          }
          *:hover > .resize-handle-indicator {
            opacity: 0.5;
          }
          *:active > .resize-handle-indicator {
            opacity: 0.8;
          }
        `}
      </style>
    </div>
  );
};

// PropTypes for ResizableColumns
ResizableColumns.propTypes = {
  columns: PropTypes.number.isRequired,
  children: PropTypes.node,
  columnSpacing: PropTypes.string,
};

ResizableColumns.defaultProps = {
  children: null,
  columnSpacing: '8px',
};

const FormView = ({ schema, formValues, onChange }) => {
  // Track expanded state for all list items across the form - default to collapsed
  const [expandedItems, setExpandedItems] = useState({});

  const getValueAtPath = (obj, path) => {
    const segments = path.split(/[.[\]]+/).filter(Boolean);

    const result = segments.reduce((acc, segment) => {
      if (acc === null || acc === undefined) {
        return undefined;
      }
      return acc[segment];
    }, obj);

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
    const currentPath = path ? `${path}.${key}` : key;
    const value = getValueAtPath(formValues, currentPath);

    if (property.type === 'list') {
      return renderListField(key, property, currentPath);
    }

    if (property.type === 'object') {
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

    // Get the section title from metadata if available
    const sectionTitle = property.sectionLabel || `${key.charAt(0).toUpperCase() + key.slice(1)} Configuration`;

    // Calculate nesting level for indentation
    const nestLevel = property.nestLevel || 0;

    // Use container with section header for all object types with sectionLabel
    if (property.sectionLabel) {
      return (
        <Container header={<Header variant="h3">{sectionTitle}</Header>}>
          <SpaceBetween size="s">
            {Object.entries(property.properties).map(([propKey, propSchema]) => {
              return <Box key={propKey}>{renderField(propKey, propSchema, fullPath)}</Box>;
            })}
          </SpaceBetween>
        </Container>
      );
    }

    // Default compact layout for nested objects without sectionLabel
    return (
      <Box padding="s">
        <SpaceBetween size="xs">
          {Object.entries(property.properties).map(([propKey, propSchema]) => {
            const nestedPropSchema =
              propSchema.type === 'list' ? { ...propSchema, nestLevel: nestLevel + 1 } : propSchema;
            return <Box key={propKey}>{renderField(propKey, nestedPropSchema, fullPath)}</Box>;
          })}
        </SpaceBetween>
      </Box>
    );
  }

  function renderListField(key, property, path) {
    const values = getValueAtPath(formValues, path) || [];

    // Get list item display settings from schema metadata
    const columnCount = property.columns ? parseInt(property.columns, 10) : 2;
    const nestLevel = property.nestLevel || 0;
    const nextNestLevel = nestLevel + 1;

    // Get list labels
    const listLabel = property.listLabel || key.charAt(0).toUpperCase() + key.slice(1);
    const itemLabel = property.itemLabel || key.charAt(0).toUpperCase() + key.slice(1).replace(/s$/, '');

    // Create unique key for this list's expanded state
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
        padding={{ left: `${nestLevel * 16}px`, top: 'xs', bottom: 'xs' }}
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
          {listLabel}
        </Box>
      </Box>
    );

    // List content with items - only shown when expanded
    const itemsContent = isListExpanded && (
      <Box padding={{ left: `${nestLevel * 16}px` }}>
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
                {/* Item row with delete button */}
                <Box display="flex" alignItems="flex-start" padding={{ top: 'xxxs', bottom: 'xxxs' }}>
                  {/* Content area with property fields and nested lists */}
                  <Box flex="1">
                    {property.items.type === 'object' ? (
                      (() => {
                        // First, get all property entries sorted by their order if available
                        const propEntries = Object.entries(property.items.properties || {})
                          .map(([propKey, prop]) => ({
                            propKey,
                            prop,
                            order: prop.order || 999,
                          }))
                          .sort((a, b) => a.order - b.order);

                        // Add debugging to see actual column count
                        console.log(`Rendering ${columnCount} columns for ${propEntries.length} properties`);

                        // Separate regular fields from list fields
                        const regularProps = [];
                        const listProps = [];

                        // Identify and separate the fields
                        propEntries.forEach(({ propKey, prop: propSchema }) => {
                          if (propSchema.type === 'list') {
                            listProps.push({ propKey, propSchema });
                          } else {
                            regularProps.push({ propKey, propSchema });
                          }
                        });

                        // Render the regular fields using HTML table for guaranteed columns
                        const renderedRegularFields = (
                          <Box padding="s">
                            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '8px 0' }}>
                              <tbody>
                                {/* Split fields into rows based on columnCount */}
                                {Array.from({ length: Math.ceil(regularProps.length / columnCount) }).map(
                                  (rowItem, rowIndex) => (
                                    <tr key={`row-${rowIndex}`}>
                                      {Array.from({ length: columnCount }).map((colItem, colIndex) => {
                                        const fieldIndex = rowIndex * columnCount + colIndex;
                                        if (fieldIndex >= regularProps.length)
                                          return <td key={`empty-${colIndex}`} aria-hidden="true" />;

                                        const { propKey, propSchema } = regularProps[fieldIndex];
                                        const propPath = `${itemPath}.${propKey}`;
                                        const propValue = getValueAtPath(formValues, propPath);

                                        return (
                                          <td
                                            key={propKey}
                                            style={{ verticalAlign: 'top', width: `${100 / columnCount}%` }}
                                          >
                                            <Box padding="xs">
                                              {renderInputField(propKey, propSchema, propValue, propPath)}
                                            </Box>
                                          </td>
                                        );
                                      })}
                                    </tr>
                                  ),
                                )}
                              </tbody>
                            </table>
                          </Box>
                        );

                        // Render any list fields (like attributes)
                        const renderedListFields = listProps.map(({ propKey, propSchema }) => {
                          const propPath = `${itemPath}.${propKey}`;

                          // Configure nested list with proper indentation
                          const nestedListProps = {
                            ...propSchema,
                            nestLevel: nextNestLevel,
                            // Explicitly set columns for the nested list
                            columns: propSchema.columns || 2,
                          };

                          return (
                            <Box key={propKey} padding={{ top: 'xxxs', bottom: 'xxxs' }} width="100%">
                              {renderListField(propKey, nestedListProps, propPath)}
                            </Box>
                          );
                        });

                        // Return both the regular fields and any list fields
                        return (
                          <Box>
                            {renderedRegularFields}
                            {renderedListFields.length > 0 && <Box padding="s">{renderedListFields}</Box>}
                          </Box>
                        );
                      })()
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
    return (
      <Box>
        {listHeader}
        {itemsContent}
      </Box>
    );
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

    // Use description as the label
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
