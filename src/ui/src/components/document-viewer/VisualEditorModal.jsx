/* eslint-disable react/prop-types */
/* eslint-disable prettier/prettier */
/* eslint-disable prefer-destructuring */
import React, { useState, useEffect, useRef, memo } from 'react';
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
const isDevelopment = process.env.NODE_ENV === 'development';

// Memoized component to render a bounding box on an image
const BoundingBox = memo(({ box, page, currentPage, imageRef, zoomLevel = 1, panOffset = { x: 0, y: 0 } }) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (imageRef.current && page === currentPage) {
      const updateDimensions = () => {
        const img = imageRef.current;
        const rect = img.getBoundingClientRect();
        const containerRect = img.parentElement.getBoundingClientRect();
        
        const width = img.width || img.naturalWidth;
        const height = img.height || img.naturalHeight;
        const offsetX = rect.left - containerRect.left;
        const offsetY = rect.top - containerRect.top;
        
        setDimensions({
          width,
          height,
          offsetX,
          offsetY,
        });
        
        if (isDevelopment) {
          console.log('VisualEditorModal - BoundingBox dimensions updated:', {
            imageWidth: img.width,
            imageHeight: img.height,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            offsetX: rect.left - containerRect.left,
            offsetY: rect.top - containerRect.top,
            imageRect: rect,
            containerRect
          });
        }
      };

      // Update dimensions when image loads
      if (imageRef.current.complete && imageRef.current.naturalWidth > 0) {
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

  // Calculate position based on image dimensions with proper zoom and pan handling
  let style = {};

  if (box.boundingBox) {
    // Handle both uppercase and lowercase property names
    const bbox = box.boundingBox;
    const left = bbox.left || bbox.Left || 0;
    const top = bbox.top || bbox.Top || 0;
    const width = bbox.width || bbox.Width || 0;
    const height = bbox.height || bbox.Height || 0;
    
    // Account for image offset within container
    const offsetX = dimensions.offsetX || 0;
    const offsetY = dimensions.offsetY || 0;
    
    // Calculate base position and size relative to image
    const baseLeft = left * dimensions.width + offsetX;
    const baseTop = top * dimensions.height + offsetY;
    const baseWidth = width * dimensions.width;
    const baseHeight = height * dimensions.height;
    
    // Calculate the center of the image for transform origin reference
    const imageCenterX = offsetX + dimensions.width / 2;
    const imageCenterY = offsetY + dimensions.height / 2;
    
    // Calculate bounding box center relative to image center
    const boxCenterX = baseLeft + baseWidth / 2;
    const boxCenterY = baseTop + baseHeight / 2;
    const relativeX = boxCenterX - imageCenterX;
    const relativeY = boxCenterY - imageCenterY;
    
    // Apply zoom transformation to the relative position
    const scaledRelativeX = relativeX * zoomLevel;
    const scaledRelativeY = relativeY * zoomLevel;
    
    // Calculate final position after zoom and pan
    const finalCenterX = imageCenterX + scaledRelativeX + panOffset.x;
    const finalCenterY = imageCenterY + scaledRelativeY + panOffset.y;
    
    // Calculate final bounding box position (top-left corner)
    const finalLeft = finalCenterX - (baseWidth * zoomLevel) / 2;
    const finalTop = finalCenterY - (baseHeight * zoomLevel) / 2;
    
    style = {
      position: 'absolute',
      left: `${finalLeft}px`,
      top: `${finalTop}px`,
      width: `${baseWidth * zoomLevel}px`,
      height: `${baseHeight * zoomLevel}px`,
      border: '2px solid red',
      pointerEvents: 'none',
      zIndex: 10,
      transition: 'all 0.1s ease-out'
    };
    
    if (isDevelopment) {
      console.log('VisualEditorModal - BoundingBox style calculated:', {
        bbox,
        dimensions,
        offsetX,
        offsetY,
        zoomLevel,
        panOffset,
        baseLeft,
        baseTop,
        imageCenterX,
        imageCenterY,
        boxCenterX,
        boxCenterY,
        relativeX,
        relativeY,
        scaledRelativeX,
        scaledRelativeY,
        finalCenterX,
        finalCenterY,
        finalLeft,
        finalTop,
        style
      });
    }
  } else if (box.vertices) {
    // Format: array of {x, y} or {X, Y} points
    const xs = box.vertices.map((v) => v.x || v.X || 0);
    const ys = box.vertices.map((v) => v.y || v.Y || 0);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);
    
    // Account for image offset within container
    const offsetX = dimensions.offsetX || 0;
    const offsetY = dimensions.offsetY || 0;

    // Calculate base position and size relative to image
    const baseLeft = minX * dimensions.width + offsetX;
    const baseTop = minY * dimensions.height + offsetY;
    const baseWidth = (maxX - minX) * dimensions.width;
    const baseHeight = (maxY - minY) * dimensions.height;
    
    // Calculate the center of the image for transform origin reference
    const imageCenterX = offsetX + dimensions.width / 2;
    const imageCenterY = offsetY + dimensions.height / 2;
    
    // Calculate bounding box center relative to image center
    const boxCenterX = baseLeft + baseWidth / 2;
    const boxCenterY = baseTop + baseHeight / 2;
    const relativeX = boxCenterX - imageCenterX;
    const relativeY = boxCenterY - imageCenterY;
    
    // Apply zoom transformation to the relative position
    const scaledRelativeX = relativeX * zoomLevel;
    const scaledRelativeY = relativeY * zoomLevel;
    
    // Calculate final position after zoom and pan
    const finalCenterX = imageCenterX + scaledRelativeX + panOffset.x;
    const finalCenterY = imageCenterY + scaledRelativeY + panOffset.y;
    
    // Calculate final bounding box position (top-left corner)
    const finalLeft = finalCenterX - (baseWidth * zoomLevel) / 2;
    const finalTop = finalCenterY - (baseHeight * zoomLevel) / 2;

    style = {
      position: 'absolute',
      left: `${finalLeft}px`,
      top: `${finalTop}px`,
      width: `${baseWidth * zoomLevel}px`,
      height: `${baseHeight * zoomLevel}px`,
      border: '2px solid red',
      pointerEvents: 'none',
      zIndex: 10,
      transition: 'all 0.1s ease-out'
    };
    
    if (isDevelopment) {
      console.log('VisualEditorModal - BoundingBox style (vertices) calculated:', {
        vertices: box.vertices,
        dimensions,
        offsetX,
        offsetY,
        zoomLevel,
        panOffset,
        baseLeft,
        baseTop,
        imageCenterX,
        imageCenterY,
        boxCenterX,
        boxCenterY,
        relativeX,
        relativeY,
        scaledRelativeX,
        scaledRelativeY,
        finalCenterX,
        finalCenterY,
        finalLeft,
        finalTop,
        style
      });
    }
  }

  return <div style={style} />;
});

// Component to render a form field based on its type
const FormFieldRenderer = ({
  fieldKey,
  value,
  onChange,
  isReadOnly,
  confidence,
  geometry,
  onFieldFocus,
  onFieldDoubleClick,
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
    const fullPath = `${path.join('.')}${path.length > 0 ? '.' : ''}${fieldKey}`;
    console.log('Full Path:', fullPath);
    console.log('Field Value:', value);
    console.log('Geometry Passed:', geometry);
    console.log('Explainability Info Available:', !!explainabilityInfo);
    
    let actualGeometry = geometry;
    
    // Try to extract geometry from explainabilityInfo if not provided
    if (!actualGeometry && explainabilityInfo && Array.isArray(explainabilityInfo) && explainabilityInfo[0]) {
      const [firstExplainabilityItem] = explainabilityInfo;
      console.log('Explainability Info Object:', firstExplainabilityItem);
      
      // Try direct field lookup first
      let fieldInfo = firstExplainabilityItem[fieldKey];
      console.log(`Field Info from explainabilityInfo[0][${fieldKey}]:`, fieldInfo);
      
      // If not found directly, try to navigate the full path
      if (!fieldInfo) {
        console.log('Trying to navigate full path in explainabilityInfo:', fullPath);
        const fullPathParts = [...path, fieldKey];
        let pathFieldInfo = firstExplainabilityItem;
        
        fullPathParts.forEach((pathPart, index) => {
          console.log(`Navigating path part ${index}: ${pathPart}`);
          console.log('Current pathFieldInfo:', pathFieldInfo);
          
          if (pathFieldInfo && typeof pathFieldInfo === 'object') {
            if (Array.isArray(pathFieldInfo) && !Number.isNaN(parseInt(pathPart, 10))) {
              // Handle array index
              const arrayIndex = parseInt(pathPart, 10);
              if (arrayIndex >= 0 && arrayIndex < pathFieldInfo.length) {
                pathFieldInfo = pathFieldInfo[arrayIndex];
                console.log(`Found array item at index ${arrayIndex}:`, pathFieldInfo);
              } else {
                console.log(`Array index ${arrayIndex} out of bounds`);
                pathFieldInfo = null;
              }
            } else if (pathFieldInfo[pathPart]) {
              // Handle object property
              pathFieldInfo = pathFieldInfo[pathPart];
              console.log(`Found object property ${pathPart}:`, pathFieldInfo);
            } else {
              console.log(`Property ${pathPart} not found in object`);
              pathFieldInfo = null;
            }
          } else {
            console.log(`Cannot navigate further - pathFieldInfo is not an object`);
            pathFieldInfo = null;
          }
        });
        
        fieldInfo = pathFieldInfo;
        console.log('Final fieldInfo from path navigation:', fieldInfo);
      }
      
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

  // Handle field double-click
  const handleDoubleClick = (event) => {
    if (event) {
      event.stopPropagation();
    }
    console.log('=== FIELD DOUBLE-CLICKED ===');
    console.log('Field Key:', fieldKey);
    console.log('Geometry Passed:', geometry);
    
    let actualGeometry = geometry;
    
    // Try to extract geometry from explainabilityInfo if not provided
    if (!actualGeometry && explainabilityInfo && Array.isArray(explainabilityInfo) && explainabilityInfo[0]) {
      const [firstExplainabilityItem] = explainabilityInfo;
      const fieldInfo = firstExplainabilityItem[fieldKey];
      
      if (fieldInfo && fieldInfo.geometry && Array.isArray(fieldInfo.geometry) && fieldInfo.geometry[0]) {
        actualGeometry = fieldInfo.geometry[0];
      }
    }
    
    if (actualGeometry && onFieldDoubleClick) {
      console.log('Calling onFieldDoubleClick with geometry:', actualGeometry);
      onFieldDoubleClick(actualGeometry);
    } else {
      console.log('No geometry found for field double-click:', fieldKey);
    }
    console.log('=== END FIELD DOUBLE-CLICK ===');
  };

  // Render based on field type
  switch (fieldType) {
    case 'string':
      return (
        <div
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
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
        <div
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleClick(e);
            }
          }}
          role="button"
          tabIndex={0}
          style={{ cursor: geometry ? 'pointer' : 'default' }}
        >
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
        </div>
      );

    case 'boolean':
      return (
        <div
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleClick(e);
            }
          }}
          role="button"
          tabIndex={0}
          style={{ cursor: geometry ? 'pointer' : 'default' }}
        >
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
        </div>
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
                    key={`obj-${fieldKey}-${path.join('.')}-${key}-${Date.now()}-${Math.random()}`}
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
                    onFieldDoubleClick={onFieldDoubleClick}
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
                // Create a unique key for each array item with timestamp and random component
                const itemKey = `arr-${fieldKey}-${path.join('.')}-${index}-${Date.now()}-${Math.random()}`;

                // Extract confidence and geometry for array items
                let itemConfidence;
                let itemGeometry;
                
                // Try to get from explainability_info if available
                if (explainabilityInfo && Array.isArray(explainabilityInfo)) {
                  const [firstExplainabilityItem] = explainabilityInfo;
                  
                  // Handle nested structure - navigate to the array field first
                  let arrayFieldInfo = firstExplainabilityItem;
                  path.forEach((pathPart) => {
                    if (arrayFieldInfo && typeof arrayFieldInfo === 'object' && arrayFieldInfo[pathPart]) {
                      arrayFieldInfo = arrayFieldInfo[pathPart];
                    } else {
                      arrayFieldInfo = null;
                    }
                  });
                  
                  // For arrays, the explainability info structure can be:
                  // 1. An array where each element has confidence/geometry (e.g., ENDORSEMENTS, RESTRICTIONS)
                  // 2. An object with nested structure
                  if (arrayFieldInfo && Array.isArray(arrayFieldInfo) && arrayFieldInfo[index]) {
                    const itemInfo = arrayFieldInfo[index];
                    if (itemInfo) {
                      itemConfidence = itemInfo.confidence;
                      
                      // Extract geometry
                      if (itemInfo.geometry && Array.isArray(itemInfo.geometry) && itemInfo.geometry.length > 0) {
                        const geomData = itemInfo.geometry[0];
                        if (geomData.boundingBox && geomData.page !== undefined) {
                          itemGeometry = {
                            boundingBox: geomData.boundingBox,
                            page: geomData.page,
                            vertices: geomData.vertices
                          };
                        }
                      }
                    }
                  }
                }

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
                    confidence={itemConfidence}
                    geometry={itemGeometry}
                    onFieldFocus={onFieldFocus}
                    onFieldDoubleClick={onFieldDoubleClick}
                    path={[...path, index]}
                    explainabilityInfo={explainabilityInfo}
                  />
                );
              })}
            </SpaceBetween>
          </Box>
        </Box>
      );

    default:
      return (
        <div
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleClick(e);
            }
          }}
          role="button"
          tabIndex={0}
          style={{ cursor: geometry ? 'pointer' : 'default' }}
        >
          <FormField label={label}>
            <Input
              value={String(value)}
              disabled={isReadOnly}
              onChange={({ detail }) => !isReadOnly && onChange(detail.value)}
              onFocus={handleFocus}
            />
          </FormField>
        </div>
      );
  }
};

const VisualEditorModal = ({ visible, onDismiss, jsonData, onChange, isReadOnly, sectionData }) => {
  const { currentCredentials } = useAppContext();
  const [pageImages, setPageImages] = useState({});
  const [loadingImages, setLoadingImages] = useState(true);
  const [currentPage, setCurrentPage] = useState(null);
  const [activeFieldGeometry, setActiveFieldGeometry] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const imageRef = useRef(null);
  const imageContainerRef = useRef(null);

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

  // Zoom controls
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.25, 4));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.25, 0.25));
  };

  // Pan controls
  const panStep = 50;
  
  const handlePanLeft = () => {
    setPanOffset(prev => ({ ...prev, x: prev.x + panStep }));
  };

  const handlePanRight = () => {
    setPanOffset(prev => ({ ...prev, x: prev.x - panStep }));
  };

  const handlePanUp = () => {
    setPanOffset(prev => ({ ...prev, y: prev.y + panStep }));
  };

  const handlePanDown = () => {
    setPanOffset(prev => ({ ...prev, y: prev.y - panStep }));
  };

  const handleResetView = () => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  };

  // Handle mouse wheel for zoom
  const handleWheel = (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 1.1 : 0.9;
      setZoomLevel(prev => Math.min(Math.max(prev * delta, 0.25), 4));
    }
  };

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

  // Handle field double-click - zoom to 200% and center on field
  const handleFieldDoubleClick = (geometry) => {
    console.log('VisualEditorModal - handleFieldDoubleClick called with geometry:', geometry);
    
    if (geometry && imageRef.current && imageContainerRef.current) {
      // First switch to the correct page if needed
      if (geometry.page !== undefined && pageIds.length > 0) {
        const pageIndex = geometry.page - 1;
        if (pageIndex >= 0 && pageIndex < pageIds.length) {
          const targetPageId = pageIds[pageIndex];
          if (targetPageId !== currentPage) {
            setCurrentPage(targetPageId);
          }
        }
      }

      // Set zoom to 200%
      const targetZoom = 2.0;
      setZoomLevel(targetZoom);
      
      // Calculate pan offset to center the field
      setTimeout(() => {
        if (imageRef.current && imageContainerRef.current) {
          const img = imageRef.current;
          const container = imageContainerRef.current;
          
          // Get image and container dimensions
          const imgRect = img.getBoundingClientRect();
          const containerRect = container.getBoundingClientRect();
          
          const imageWidth = img.width || img.naturalWidth;
          const imageHeight = img.height || img.naturalHeight;
          const offsetX = imgRect.left - containerRect.left;
          const offsetY = imgRect.top - containerRect.top;
          
          // Get bounding box coordinates
          let bbox;
          if (geometry.boundingBox) {
            bbox = geometry.boundingBox;
          } else if (geometry.vertices) {
            const xs = geometry.vertices.map((v) => v.x || v.X || 0);
            const ys = geometry.vertices.map((v) => v.y || v.Y || 0);
            bbox = {
              left: Math.min(...xs),
              top: Math.min(...ys),
              width: Math.max(...xs) - Math.min(...xs),
              height: Math.max(...ys) - Math.min(...ys)
            };
          }
          
          if (bbox) {
            const left = bbox.left || bbox.Left || 0;
            const top = bbox.top || bbox.Top || 0;
            const width = bbox.width || bbox.Width || 0;
            const height = bbox.height || bbox.Height || 0;
            
            // Calculate field center in image coordinates
            const fieldCenterX = (left + width / 2) * imageWidth + offsetX;
            const fieldCenterY = (top + height / 2) * imageHeight + offsetY;
            
            // Calculate viewport center
            const viewportCenterX = containerRect.width / 2;
            const viewportCenterY = containerRect.height / 2;
            
            // Calculate image center
            const imageCenterX = offsetX + imageWidth / 2;
            const imageCenterY = offsetY + imageHeight / 2;
            
            // Calculate relative position of field center from image center
            const relativeX = fieldCenterX - imageCenterX;
            const relativeY = fieldCenterY - imageCenterY;
            
            // At 200% zoom, calculate where the field center will be
            const scaledRelativeX = relativeX * targetZoom;
            const scaledRelativeY = relativeY * targetZoom;
            
            // Calculate required pan offset to center the field in viewport
            const requiredPanX = viewportCenterX - (imageCenterX + scaledRelativeX);
            const requiredPanY = viewportCenterY - (imageCenterY + scaledRelativeY);
            
            console.log('VisualEditorModal - Auto-centering calculation:', {
              fieldCenterX, fieldCenterY,
              viewportCenterX, viewportCenterY,
              imageCenterX, imageCenterY,
              relativeX, relativeY,
              scaledRelativeX, scaledRelativeY,
              requiredPanX, requiredPanY
            });
            
            setPanOffset({ x: requiredPanX, y: requiredPanY });
          }
        }
      }, 100); // Small delay to allow zoom to take effect
      
      // Also set the active geometry for bounding box display
      setActiveFieldGeometry(geometry);
    }
  };

  // Create carousel items from page images
  const carouselItems = pageIds.map((pageId) => ({
    id: pageId,
    content: (
      <div 
        ref={pageId === currentPage ? imageContainerRef : null}
        style={{ 
          position: 'relative', 
          width: '100%', 
          height: '100%', 
          display: 'flex', 
          justifyContent: 'center',
          overflow: 'hidden',
          cursor: zoomLevel > 1 ? 'grab' : 'default'
        }}
        onWheel={handleWheel}
      >
        {pageImages[pageId] ? (
          <>
            <img
              ref={pageId === currentPage ? imageRef : null}
              src={pageImages[pageId]}
              alt={`Page ${pageId}`}
              style={{ 
                maxWidth: zoomLevel === 1 ? '100%' : 'none',
                maxHeight: zoomLevel === 1 ? 'calc(100vh - 200px)' : 'none',
                objectFit: 'contain',
                transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
                transformOrigin: 'center center',
                transition: 'transform 0.1s ease-out'
              }}
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
                zoomLevel={zoomLevel}
                panOffset={panOffset}
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

                    {/* Page indicator and Controls */}
                    <Box
                      style={{
                        position: 'absolute',
                        bottom: '10px',
                        width: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      {/* Page indicator */}
                      <Box
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.8)',
                          padding: '4px 8px',
                          borderRadius: '4px',
                        }}
                      >
                        Page {pageIds.indexOf(currentPage) + 1} of {pageIds.length}
                      </Box>
                      
                      {/* Zoom and Pan Controls */}
                      <Box
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          boxShadow: '0 1px 4px rgba(0, 0, 0, 0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '12px'
                        }}
                      >
                        <span style={{ fontWeight: 'bold' }}>Zoom:</span>
                        <span
                          onClick={handleZoomOut}
                          onKeyDown={(e) => e.key === 'Enter' && handleZoomOut()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel <= 0.25 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel <= 0.25 ? 0.5 : 1,
                            fontSize: '14px',
                            fontWeight: 'bold',
                            userSelect: 'none',
                            padding: '2px 4px'
                          }}
                          title="Zoom Out"
                        >
                          −
                        </span>
                        <span style={{ fontSize: '12px', minWidth: '30px', textAlign: 'center' }}>
                          {Math.round(zoomLevel * 100)}%
                        </span>
                        <span
                          onClick={handleZoomIn}
                          onKeyDown={(e) => e.key === 'Enter' && handleZoomIn()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel >= 4 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel >= 4 ? 0.5 : 1,
                            fontSize: '14px',
                            fontWeight: 'bold',
                            userSelect: 'none',
                            padding: '2px 4px'
                          }}
                          title="Zoom In"
                        >
                          +
                        </span>
                        <span style={{ fontWeight: 'bold', marginLeft: '4px' }}>Pan:</span>
                        <span
                          onClick={handlePanLeft}
                          onKeyDown={(e) => e.key === 'Enter' && handlePanLeft()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel <= 1 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel <= 1 ? 0.5 : 1,
                            fontSize: '14px',
                            userSelect: 'none',
                            padding: '2px 3px'
                          }}
                          title="Pan Left"
                        >
                          ←
                        </span>
                        <span
                          onClick={handlePanRight}
                          onKeyDown={(e) => e.key === 'Enter' && handlePanRight()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel <= 1 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel <= 1 ? 0.5 : 1,
                            fontSize: '14px',
                            userSelect: 'none',
                            padding: '2px 3px'
                          }}
                          title="Pan Right"
                        >
                          →
                        </span>
                        <span
                          onClick={handlePanUp}
                          onKeyDown={(e) => e.key === 'Enter' && handlePanUp()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel <= 1 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel <= 1 ? 0.5 : 1,
                            fontSize: '14px',
                            userSelect: 'none',
                            padding: '2px 3px'
                          }}
                          title="Pan Up"
                        >
                          ↑
                        </span>
                        <span
                          onClick={handlePanDown}
                          onKeyDown={(e) => e.key === 'Enter' && handlePanDown()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: zoomLevel <= 1 ? 'not-allowed' : 'pointer',
                            opacity: zoomLevel <= 1 ? 0.5 : 1,
                            fontSize: '14px',
                            userSelect: 'none',
                            padding: '2px 3px'
                          }}
                          title="Pan Down"
                        >
                          ↓
                        </span>
                        <span
                          onClick={handleResetView}
                          onKeyDown={(e) => e.key === 'Enter' && handleResetView()}
                          role="button"
                          tabIndex={0}
                          style={{
                            cursor: 'pointer',
                            fontSize: '12px',
                            userSelect: 'none',
                            padding: '2px 3px',
                            marginLeft: '2px'
                          }}
                          title="Reset View"
                        >
                          ⟲
                        </span>
                      </Box>
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
                    onFieldDoubleClick={handleFieldDoubleClick}
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
