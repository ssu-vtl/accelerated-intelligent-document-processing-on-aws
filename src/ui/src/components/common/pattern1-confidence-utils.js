// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * Pattern-1 specific confidence utilities for BDA processing
 */

/**
 * Get overall confidence information for Pattern-1 documents
 * @param {Object} document - Document object
 * @param {number} confidenceThreshold - Overall confidence threshold
 * @returns {Object} Confidence information with display properties
 */
export const getPattern1ConfidenceInfo = (document, confidenceThreshold = 0.8) => {
  if (!document || !document.sections || !Array.isArray(document.sections)) {
    return { hasConfidenceInfo: false };
  }

  // For Pattern-1, we look at overall document confidence
  // This includes blueprint confidence and key-value confidences
  let overallConfidence = null;
  let blueprintConfidence = null;
  let keyValueConfidences = [];
  let hitlTriggered = false;

  // Extract confidence information from document sections
  document.sections.forEach(section => {
    if (section.attributes) {
      // Look for blueprint confidence
      if (section.attributes.extraction_bp_name && section.attributes.bp_confidence) {
        blueprintConfidence = parseFloat(section.attributes.bp_confidence);
      }
      
      // Look for HITL status
      if (section.attributes.hitl_triggered !== undefined) {
        hitlTriggered = section.attributes.hitl_triggered;
      }
      
      // Extract key-value confidences from explainability data
      if (section.explainability_info && Array.isArray(section.explainability_info)) {
        section.explainability_info.forEach(explainData => {
          if (explainData && typeof explainData === 'object') {
            Object.entries(explainData).forEach(([key, value]) => {
              if (value && typeof value === 'object' && typeof value.confidence === 'number') {
                keyValueConfidences.push({
                  field: key,
                  confidence: value.confidence,
                  threshold: confidenceThreshold
                });
              }
            });
          }
        });
      }
    }
  });

  // Calculate overall confidence (minimum of blueprint and key-value confidences)
  const allConfidences = [];
  if (blueprintConfidence !== null) {
    allConfidences.push(blueprintConfidence);
  }
  keyValueConfidences.forEach(kv => allConfidences.push(kv.confidence));
  
  if (allConfidences.length > 0) {
    overallConfidence = Math.min(...allConfidences);
  }

  if (overallConfidence === null) {
    return { hasConfidenceInfo: false };
  }

  const isAboveThreshold = overallConfidence >= confidenceThreshold;
  
  return {
    hasConfidenceInfo: true,
    overallConfidence,
    blueprintConfidence,
    keyValueConfidences,
    confidenceThreshold,
    isAboveThreshold,
    hitlTriggered,
    shouldHighlight: !isAboveThreshold || hitlTriggered,
    textColor: getConfidenceColor(overallConfidence, confidenceThreshold),
    displayMode: 'overall-confidence',
    confidenceLevel: getConfidenceLevel(overallConfidence, confidenceThreshold)
  };
};

/**
 * Get color based on confidence score and threshold
 * @param {number} confidence - Confidence score
 * @param {number} threshold - Confidence threshold
 * @returns {string} Color code
 */
export const getConfidenceColor = (confidence, threshold) => {
  if (confidence >= threshold) {
    return '#16794d'; // Green - good confidence
  } else if (confidence >= threshold * 0.8) {
    return '#ff9500'; // Orange - medium confidence
  } else {
    return '#d13313'; // Red - low confidence
  }
};

/**
 * Get confidence level description
 * @param {number} confidence - Confidence score
 * @param {number} threshold - Confidence threshold
 * @returns {string} Confidence level
 */
export const getConfidenceLevel = (confidence, threshold) => {
  if (confidence >= threshold) {
    return 'high';
  } else if (confidence >= threshold * 0.8) {
    return 'medium';
  } else {
    return 'low';
  }
};

/**
 * Check if document should trigger HITL based on confidence
 * @param {Object} document - Document object
 * @param {number} confidenceThreshold - Confidence threshold
 * @returns {boolean} Whether HITL should be triggered
 */
export const shouldTriggerHITL = (document, confidenceThreshold) => {
  const confidenceInfo = getPattern1ConfidenceInfo(document, confidenceThreshold);
  return confidenceInfo.hasConfidenceInfo && !confidenceInfo.isAboveThreshold;
};

/**
 * Format confidence score for display
 * @param {number} confidence - Confidence score
 * @param {boolean} asPercentage - Whether to format as percentage
 * @returns {string} Formatted confidence score
 */
export const formatConfidenceScore = (confidence, asPercentage = true) => {
  if (typeof confidence !== 'number') {
    return 'N/A';
  }
  
  if (asPercentage) {
    return `${(confidence * 100).toFixed(1)}%`;
  } else {
    return confidence.toFixed(3);
  }
};

/**
 * Get confidence summary for Pattern-1 document
 * @param {Object} document - Document object
 * @param {number} confidenceThreshold - Confidence threshold
 * @returns {Object} Confidence summary with details
 */
export const getPattern1ConfidenceSummary = (document, confidenceThreshold) => {
  const confidenceInfo = getPattern1ConfidenceInfo(document, confidenceThreshold);
  
  if (!confidenceInfo.hasConfidenceInfo) {
    return {
      hasInfo: false,
      message: 'No confidence information available'
    };
  }

  const summary = {
    hasInfo: true,
    overallConfidence: confidenceInfo.overallConfidence,
    confidenceLevel: confidenceInfo.confidenceLevel,
    isAboveThreshold: confidenceInfo.isAboveThreshold,
    hitlTriggered: confidenceInfo.hitlTriggered,
    details: []
  };

  // Add blueprint confidence detail
  if (confidenceInfo.blueprintConfidence !== null) {
    summary.details.push({
      type: 'blueprint',
      label: 'Blueprint Match Confidence',
      confidence: confidenceInfo.blueprintConfidence,
      isAboveThreshold: confidenceInfo.blueprintConfidence >= confidenceThreshold,
      color: getConfidenceColor(confidenceInfo.blueprintConfidence, confidenceThreshold)
    });
  }

  // Add key-value confidence details
  confidenceInfo.keyValueConfidences.forEach(kv => {
    summary.details.push({
      type: 'keyvalue',
      label: `Field: ${kv.field}`,
      confidence: kv.confidence,
      isAboveThreshold: kv.confidence >= confidenceThreshold,
      color: getConfidenceColor(kv.confidence, confidenceThreshold)
    });
  });

  return summary;
};
