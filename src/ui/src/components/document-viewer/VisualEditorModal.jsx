/* eslint-disable react/prop-types */
/* eslint-disable prettier/prettier */
/* eslint-disable prefer-destructuring */
import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  FormField,
  Input,
  Checkbox,
  Container,
  Header,
  Spinner,
  Button,
} from '@awsui/components-react';
import { Logger } from 'aws-amplify';
import generateS3PresignedUrl from '../common/generate-s3-presigned-url';
import useAppContext from '../../contexts/app';

const logger = new Logger('VisualEditorModal');

// Component to render a bounding box on an image
const BoundingBox = ({ box, page, currentPage, imageRef }) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (imageRef.current && page === currentPage) {
      const updateDimensions = () => {
        setDimensions({
          width: imageRef.current.width,
          height: imageRef.current.height,
        });
      };

      // Update dimensions when image loads
      if (imageRef.current.complete) {
        updateDimensions();
      } else {
        imageRef.current.addEventListener('load', updateDimensions);
      }

      return () => {
        if (imageRef.current) {
          imageRef.current.removeEventListener('load', updateDimensions);
        }
      };
    }
    return undefined;
  }, [imageRef, page, currentPage]);

  if (page !== currentPage || !box || !dimensions.width) {
    return null;
  }

  // Calculate position based on image dimensions
  let style = {};

  if (box.boundingBox) {
    // Handle both uppercase and lowercase property names
    const bbox = box.boundingBox;
    const left = bbox.left || bbox.Left || 0;
    const top = bbox.top || bbox.Top || 0;
    const width = bbox.width || bbox.Width || 0;
    const height = bbox.height || bbox.Height || 0;
    style = {
      position: 'absolute',
      left: `${left * dimensions.width}px`,
      top: `${top * dimensions.height}px`,
      width: `${width * dimensions.width}px`,
      height: `${height * dimensions.height}px`,
      border: '2px solid red',
      pointerEvents: 'none',
      zIndex: 10,
    };
  } else if (box.vertices) {
    // Format: array of {x, y} or {X, Y} points
    const xs = box.vertices.map((v) => v.x || v.X || 0);
    const ys = box.vertices.map((v) => v.y || v.Y || 0);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);

    style = {
      position: 'absolute',
      left: `${minX * dimensions.width}px`,
      top: `${minY * dimensions.height}px`,
      width: `${(maxX - minX) * dimensions.width}px`,
      height: `${(maxY - minY) * dimensions.height}px`,
      border: '2px solid red',
      pointerEvents: 'none',
      zIndex: 10,
    };
  }

  return <div style={style} />;
};

// Component to render a form field based on its type
const FormFieldRenderer = ({
  fieldKey,
  value,
  onChange,
  isReadOnly,
  confidence,
  geometry,
  onFieldFocus,
  path = [],
  explainabilityInfo = null,
}) => {
  // Determine field type
  let fieldType = typeof value;
  if (Array.isArray(value)) {
    fieldType = 'array';
  } else if (value === null || value === undefined) {
    fieldType = 'null';
  }

  // Create label with confidence score if available
  const label = confidence !== undefined ? `${fieldKey} (${(confidence * 100).toFixed(1)}%)` : fieldKey;

  // Handle field focus - pass geometry info if available
  const handleFocus = () => {
    if (geometry && onFieldFocus) {
      onFieldFocus(geometry);
    }
  };

  // Handle field click - debug version
  const handleClick = (event) => {
    if (event) {
      event.stopPropagation();
    }
    console.log('=== FIELD CLICKED ===');
    console.log('Field Key:', fieldKey);
    console.log('Full Path:', `${path.join('.')}${path.length > 0 ? '.' : ''}${fieldKey}`);
    console.log('Field Value:', value);
    console.log('Geometry Passed:', geometry);
    console.log('Explainability Info Available:', !!explainabilityInfo);
    
    let actualGeometry = geometry;
    
    // Try to extract geometry from explainabilityInfo if not provided
    if (!actualGeometry && explainabilityInfo && Array.isArray(explainabilityInfo) && explainabilityInfo[0]) {
      const [firstExplainabilityItem] = explainabilityInfo;
      console.log('Explainability Info Object:', firstExplainabilityItem);
      const fieldInfo = firstExplainabilityItem[fieldKey];
      console.log(`Field Info from explainabilityInfo[0][${fieldKey}]:`, fieldInfo);
      
      if (fieldInfo && fieldInfo.geometry && Array.isArray(fieldInfo.geometry) && fieldInfo.geometry[0]) {
        actualGeometry = fieldInfo.geometry[0];
        console.log('Found geometry in explainabilityInfo:', actualGeometry);
      }
      
      // Also search all keys in explainabilityInfo to find geometry
      const allKeys = Object.keys(firstExplainabilityItem);
      console.log('All available keys in explainabilityInfo:', allKeys);
    }
    
    if (actualGeometry && onFieldFocus) {
      console.log('Calling onFieldFocus with geometry:', actualGeometry);
      onFieldFocus(actualGeometry);
    } else {
      console.log('No geometry found for field:', fieldKey);
    }
    console.log('=== END FIELD CLICK ===');
  };

  // Render based on field type
  switch (fieldType) {
    case 'string':
      return (
        <div
          onClick={handleClick}
          onKeyDown={(e) => e.key === 'Enter' && handleClick(e)}
          role="button"
          tabIndex={0}
          style={{ cursor: geometry ? 'pointer' : 'default' }}
        >
          <FormField label={label}>
            <Input
              value={value || ''}
              disabled={isReadOnly}
              onChange={({ detail }) => !isReadOnly && onChange(detail.value)}
              onFocus={handleFocus}
            />
          </FormField>
        </div>
      );

    case 'number':
      return (
        <FormField label={label}>
          <Input
            type="number"
            value={String(value)}
            disabled={isReadOnly}
            onChange={({ detail }) => {
              if (!isReadOnly) {
                const numValue = Number(detail.value);
                onChange(Number.isNaN(numValue) ? 0 : numValue);
              }
            }}
            onFocus={handleFocus}
          />
        </FormField>
      );

    case 'boolean':
      return (
        <FormField label={label}>
          <Checkbox
            checked={Boolean(value)}
            disabled={isReadOnly}
            onChange={({ detail }) => !isReadOnly && onChange(detail.checked)}
            onFocus={handleFocus}
          >
            {String(value)}
          </Checkbox>
        </FormField>
      );

    case 'object':
      if (value === null) {
        return (
          <FormField label={label}>
            <Input value="null" disabled={isReadOnly} onFocus={handleFocus} />
          </FormField>
        );
      }

      return (
        <Box padding="xs">
          <Box fontSize="body-m" fontWeight="bold" padding="xxxs" onFocus={handleFocus}>
            {label}
          </Box>
          <Box padding={{ left: 'l' }}>
            <SpaceBetween size="xs">
              {Object.entries(value).map(([key, val]) => {
                // Get confidence and geometry for this field from explainability_info
                let fieldConfidence;
                let fieldGeometry;
                
                // Try to get from explainability_info if available
                if (explainabilityInfo && Array.isArray(explainabilityInfo)) {
                  // Handle nested structure like explainabilityInfo[0].NAME_DETAILS.LAST_NAME
                  const currentPath = [...path, key];
                  const [firstExplainabilityItem] = explainabilityInfo;
                  // eslint-disable-next-line prefer-destructuring
                  let fieldInfo = firstExplainabilityItem;
                  
                  // Navigate through the path to find the field info
                  let pathFieldInfo = fieldInfo;
                  currentPath.forEach((pathPart) => {
                    if (pathFieldInfo && typeof pathFieldInfo === 'object' && pathFieldInfo[pathPart]) {
                      pathFieldInfo = pathFieldInfo[pathPart];
                    } else {
                      pathFieldInfo = null;
                    }
                  });
                  fieldInfo = pathFieldInfo;
                  
                  if (fieldInfo) {
                    fieldConfidence = fieldInfo.confidence;
                    
                    // Extract geometry - handle both direct geometry and geometry arrays
                    if (fieldInfo.geometry && Array.isArray(fieldInfo.geometry) && fieldInfo.geometry.length > 0) {
                      const geomData = fieldInfo.geometry[0];
                      if (geomData.boundingBox && geomData.page !== undefined) {
                        fieldGeometry = {
                          boundingBox: geomData.boundingBox,
                          page: geomData.page,
                          vertices: geomData.vertices
                        };
                      }
                    }
                  }
                }
                
                // Also check legacy format within the value itself
                if (!fieldConfidence) {
                  fieldConfidence =
                    value.explainability_info?.confidence_scores?.[key] ||
                    value.explainability_info?.confidenceScores?.[key];
                }
                
                if (!fieldGeometry) {
                  fieldGeometry =
                    value.explainability_info?.geometry?.[key] || value.explainability_info?.geometries?.[key];
                }

                return (
                  <FormFieldRenderer
                    key={`${path.join('.')}.${key}`}
                    fieldKey={key}
                    value={val}
                    onChange={(newVal) => {
                      if (!isReadOnly) {
                        const newObj = { ...value };
                        newObj[key] = newVal;
                        onChange(newObj);
                      }
                    }}
                    isReadOnly={isReadOnly}
                    confidence={fieldConfidence}
                    geometry={fieldGeometry}
                    onFieldFocus={onFieldFocus}
                    path={[...path, key]}
                    explainabilityInfo={explainabilityInfo}
                  />
                );
              })}
            </SpaceBetween>
          </Box>
        </Box>
      );

    case 'array':
      return (
        <Box padding="xs">
          <Box fontSize="body-m" fontWeight="bold" padding="xxxs" onFocus={handleFocus}>
            {label} ({value.length} items)
          </Box>
          <Box padding={{ left: 'l' }}>
            <SpaceBetween size="xs">
              {value.map((item, index) => {
                // Create a unique key for each array item
                const itemKey = `${path.join('.')}.${index}:${JSON.stringify(item).substring(0, 20)}`;

                return (
                  <FormFieldRenderer
                    key={itemKey}
                    fieldKey={`[${index}]`}
                    value={item}
                    onChange={(newVal) => {
                      if (!isReadOnly) {
                        const newArray = [...value];
                        newArray[index] = newVal;
                        onChange(newArray);
                      }
                    }}
                    isReadOnly={isReadOnly}
                    onFieldFocus={onFieldFocus}
                    path={[...path, index]}
                  />
                );
              })}
            </SpaceBetween>
          </Box>
        </Box>
      );

    default:
      return (
        <FormField label={label}>
          <Input
            value={String(value)}
            disabled={isReadOnly}
            onChange={({ detail }) => !isReadOnly && onChange(detail.value)}
            onFocus={handleFocus}
          />
        </FormField>
      );
  }
};

const VisualEditorModal = ({ visible, onDismiss, jsonData, onChange, isReadOnly, sectionData }) => {
  const { currentCredentials } = useAppContext();
  const [pageImages, setPageImages] = useState({});
  const [loadingImages, setLoadingImages] = useState(true);
  const [currentPage, setCurrentPage] = useState(null);
  const [activeFieldGeometry, setActiveFieldGeometry] = useState(null);
  const imageRef = useRef(null);

  // Extract inference results and page IDs
  const inferenceResult = jsonData?.inference_result || jsonData?.inferenceResult || jsonData;
  const pageIds = sectionData?.PageIds || [];

  // Debug logs for sectionData
  useEffect(() => {
    logger.debug('VisualEditorModal - sectionData:', sectionData);
    logger.debug('VisualEditorModal - pageIds:', pageIds);
    logger.debug('VisualEditorModal - pages from sectionData:', sectionData?.pages);
  }, [sectionData, pageIds]);

  // Load page images
  useEffect(() => {
    if (!visible) return;

    const loadImages = async () => {
      if (!pageIds || pageIds.length === 0) {
        setLoadingImages(false);
        return;
      }

      setLoadingImages(true);

      try {
        const documentPages = sectionData?.documentItem?.pages || [];
        logger.debug('VisualEditorModal - document pages:', documentPages);
        logger.debug('VisualEditorModal - sectionData:', sectionData);
        logger.debug('VisualEditorModal - documentItem:', sectionData?.documentItem);
        logger.debug('VisualEditorModal - pageIds:', pageIds);

        const images = {};

        await Promise.all(
          pageIds.map(async (pageId) => {
            // Find the page in the document's pages array by matching the Id
            const page = documentPages.find((p) => p.Id === pageId);
            logger.debug(`VisualEditorModal - page for ID ${pageId}:`, page);

            if (page?.ImageUri) {
              try {
                logger.debug(`VisualEditorModal - generating presigned URL for ${page.ImageUri}`);
                const url = await generateS3PresignedUrl(page.ImageUri, currentCredentials);
                logger.debug(`VisualEditorModal - presigned URL generated:`, url);
                images[pageId] = url;
              } catch (err) {
                logger.error(`Error generating presigned URL for page ${pageId}:`, err);
              }
            } else {
              logger.warn(`VisualEditorModal - no ImageUri found for page ${pageId}`);

              // Try multiple fallback strategies in sequence
              let imageFound = false;

              // 1. Try to find the page in the pages array by index if pageId is a number
              const numericPageId = parseInt(pageId, 10);
              if (!imageFound && !Number.isNaN(numericPageId) && documentPages.length > numericPageId) {
                const pageByIndex = documentPages[numericPageId];
                logger.debug(`VisualEditorModal - trying page by numeric index ${numericPageId}:`, pageByIndex);
                if (pageByIndex?.ImageUri) {
                  try {
                    logger.debug(`VisualEditorModal - generating presigned URL for ${pageByIndex.ImageUri}`);
                    const url = await generateS3PresignedUrl(pageByIndex.ImageUri, currentCredentials);
                    logger.debug(`VisualEditorModal - presigned URL generated:`, url);
                    images[pageId] = url;
                    imageFound = true;
                  } catch (err) {
                    logger.error(`Error generating presigned URL for page ${pageId}:`, err);
                  }
                }
              }

              // 2. Try to use the position of pageId in the pageIds array as an index
              if (!imageFound) {
                const positionIndex = pageIds.indexOf(pageId);
                if (positionIndex !== -1 && documentPages.length > positionIndex) {
                  const pageByPosition = documentPages[positionIndex];
                  logger.debug(`VisualEditorModal - trying page by position index ${positionIndex}:`, pageByPosition);
                  if (pageByPosition?.ImageUri) {
                    try {
                      logger.debug(`VisualEditorModal - generating presigned URL for ${pageByPosition.ImageUri}`);
                      const url = await generateS3PresignedUrl(pageByPosition.ImageUri, currentCredentials);
                      logger.debug(`VisualEditorModal - presigned URL generated:`, url);
                      images[pageId] = url;
                      imageFound = true;
                    } catch (err) {
                      logger.error(`Error generating presigned URL for page ${pageId}:`, err);
                    }
                  }
                }
              }

              // 3. Last resort: try to find any page with an ImageUri
              if (!imageFound && documentPages.length > 0) {
                logger.debug(`VisualEditorModal - trying to find any page with ImageUri as last resort`);

                // Find the first page with an ImageUri
                const pageWithImage = documentPages.find((docPage) => docPage?.ImageUri);
                if (pageWithImage?.ImageUri) {
                  try {
                    logger.debug(`VisualEditorModal - generating presigned URL for ${pageWithImage.ImageUri}`);
                    const url = await generateS3PresignedUrl(pageWithImage.ImageUri, currentCredentials);
                    logger.debug(`VisualEditorModal - presigned URL generated:`, url);
                    images[pageId] = url;
                  } catch (err) {
                    logger.error(`Error generating presigned URL for fallback page:`, err);
                  }
                }
              }
            }
          }),
        );

        logger.debug('VisualEditorModal - images loaded:', images);
        setPageImages(images);

        // Set the first page as current if not already set
        if (!currentPage && pageIds.length > 0) {
          setCurrentPage(pageIds[0]);
        }
      } catch (err) {
        logger.error('Error loading page images:', err);
      } finally {
        setLoadingImages(false);
      }
    };

    loadImages();
  }, [pageIds, sectionData, currentCredentials, currentPage, visible]);

  // Handle field focus - update active field geometry and switch to the correct page
  const handleFieldFocus = (geometry) => {
    console.log('VisualEditorModal - handleFieldFocus called with geometry:', geometry);
    console.log('VisualEditorModal - pageIds:', pageIds);
    console.log('VisualEditorModal - currentPage:', currentPage);
    
    if (geometry) {
      setActiveFieldGeometry(geometry);

      // If geometry has a page field, switch to that page
      // geometry.page is 1-based and refers to the page within this section
      // pageIds contains the actual document page IDs for this section
      if (geometry.page !== undefined && pageIds.length > 0) {
        // Map geometry page (1-based) to pageIds array index (0-based)
        const pageIndex = geometry.page - 1;
        if (pageIndex >= 0 && pageIndex < pageIds.length) {
          const targetPageId = pageIds[pageIndex];
          console.log('VisualEditorModal - Setting currentPage to:', targetPageId);
          setCurrentPage(targetPageId);
        }
      }
    } else {
      setActiveFieldGeometry(null);
    }
  };

  // Create carousel items from page images
  const carouselItems = pageIds.map((pageId) => ({
    id: pageId,
    content: (
      <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', justifyContent: 'center' }}>
        {pageImages[pageId] ? (
          <>
            <img
              ref={pageId === currentPage ? imageRef : null}
              src={pageImages[pageId]}
              alt={`Page ${pageId}`}
              style={{ maxWidth: '100%', maxHeight: 'calc(100vh - 200px)', objectFit: 'contain' }}
              onError={(e) => {
                logger.error(`Error loading image for page ${pageId}:`, e);
                // Fallback image for error state
                const fallbackImage =
                  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6' +
                  'Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Yw' +
                  'ZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAi' +
                  'IHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM5OTkiPkltYWdlIGxvYWQgZXJyb3I8L3RleHQ+PC9zdmc+';
                e.target.src = fallbackImage;
              }}
            />
            {activeFieldGeometry && (
              <BoundingBox
                box={activeFieldGeometry}
                page={currentPage} 
                currentPage={currentPage}
                imageRef={imageRef}
              />
            )}
          </>
        ) : (
          <Box padding="xl" textAlign="center">
            <Spinner />
            <div>Loading image...</div>
          </Box>
        )}
      </div>
    ),
  }));

  return (
    <Modal
      onDismiss={onDismiss}
      visible={visible}
      header="Visual Document Editor"
      size="max"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDismiss}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onDismiss}>
              Done
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '20px',
          height: 'calc(100vh - 200px)',
          maxHeight: '800px',
          minHeight: '600px',
          width: '100%',
        }}
      >
        {/* Left side - Page images carousel - Fixed height, non-scrollable */}
        <div
          style={{
            width: '50%',
            minWidth: '50%',
            maxWidth: '50%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            flex: '0 0 50%',
          }}
        >
          <Container
            header={<Header variant="h3">Document Pages ({pageIds.length})</Header>}
            style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              flex: 1,
            }}
          >
            {(() => {
              if (loadingImages) {
                return (
                  <Box padding="xl" textAlign="center">
                    <Spinner />
                    <div>Loading page images...</div>
                  </Box>
                );
              }
              if (carouselItems.length > 0) {
                return (
                  <Box style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
                    {/* Display current page */}
                    {carouselItems.find((item) => item.id === currentPage)?.content}

                    {/* Simple navigation */}
                    <Box
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        position: 'absolute',
                        width: '100%',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        pointerEvents: 'none',
                      }}
                    >
                      <Button
                        iconName="angle-left"
                        variant="icon"
                        onClick={() => {
                          const currentIndex = pageIds.indexOf(currentPage);
                          if (currentIndex > 0) {
                            setCurrentPage(pageIds[currentIndex - 1]);
                            setActiveFieldGeometry(null);
                          }
                        }}
                        disabled={pageIds.indexOf(currentPage) === 0}
                        style={{ pointerEvents: 'auto' }}
                      />
                      <Button
                        iconName="angle-right"
                        variant="icon"
                        onClick={() => {
                          const currentIndex = pageIds.indexOf(currentPage);
                          if (currentIndex < pageIds.length - 1) {
                            setCurrentPage(pageIds[currentIndex + 1]);
                            setActiveFieldGeometry(null);
                          }
                        }}
                        disabled={pageIds.indexOf(currentPage) === pageIds.length - 1}
                        style={{ pointerEvents: 'auto' }}
                      />
                    </Box>

                    {/* Page indicator */}
                    <Box
                      style={{
                        position: 'absolute',
                        bottom: '10px',
                        width: '100%',
                        textAlign: 'center',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        padding: '4px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      Page {pageIds.indexOf(currentPage) + 1} of {pageIds.length}
                    </Box>
                  </Box>
                );
              }
              return (
                <Box padding="xl" textAlign="center">
                  No page images available
                </Box>
              );
            })()}
          </Container>
        </div>

        {/* Right side - Form fields - Independently scrollable */}
        <div
          style={{
            width: '50%',
            minWidth: '50%',
            maxWidth: '50%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            flex: '0 0 50%',
            overflow: 'hidden',
          }}
        >
          <Container
            header={<Header variant="h3">Document Data</Header>}
            style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              flex: 1,
            }}
          >
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: '16px',
                boxSizing: 'border-box',
                maxHeight: '800px',
                minHeight: '600px',
              }}
            >
              <Box style={{ minHeight: 'fit-content' }}>
                {inferenceResult ? (
                  <FormFieldRenderer
                    fieldKey="Document Data"
                    value={inferenceResult}
                    onChange={(newValue) => {
                      if (onChange && !isReadOnly) {
                        // Update the inference_result in the JSON data
                        const updatedData = { ...jsonData };
                        if (updatedData.inference_result) {
                          updatedData.inference_result = newValue;
                        } else if (updatedData.inferenceResult) {
                          updatedData.inferenceResult = newValue;
                        } else {
                          // If there's no inference_result field, update the entire object
                          Object.keys(updatedData).forEach((key) => {
                            delete updatedData[key];
                          });
                          Object.keys(newValue).forEach((key) => {
                            updatedData[key] = newValue[key];
                          });
                        }

                        try {
                          const jsonString = JSON.stringify(updatedData, null, 2);
                          onChange(jsonString);
                        } catch (error) {
                          logger.error('Error stringifying JSON:', error);
                        }
                      }
                    }}
                    isReadOnly={isReadOnly}
                    onFieldFocus={handleFieldFocus}
                    explainabilityInfo={jsonData?.explainability_info}
                  />
                ) : (
                  <Box padding="xl" textAlign="center">
                    No data available
                  </Box>
                )}
              </Box>
            </div>
          </Container>
        </div>
      </div>
    </Modal>
  );
};

export default VisualEditorModal;
