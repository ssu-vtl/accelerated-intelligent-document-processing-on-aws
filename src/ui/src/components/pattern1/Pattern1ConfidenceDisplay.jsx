// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React, { useState } from 'react';
import { 
  getPattern1ConfidenceInfo, 
  getPattern1ConfidenceSummary,
  formatConfidenceScore 
} from '../common/pattern1-confidence-utils';

/**
 * Pattern-1 specific confidence display component
 */
const Pattern1ConfidenceDisplay = ({ 
  document, 
  confidenceThreshold = 0.8,
  onTriggerHITL 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);

  const confidenceInfo = getPattern1ConfidenceInfo(document, confidenceThreshold);
  const confidenceSummary = getPattern1ConfidenceSummary(document, confidenceThreshold);

  if (!confidenceInfo.hasConfidenceInfo) {
    return (
      <div className="confidence-display pattern1-confidence">
        <div className="confidence-header">
          <span className="confidence-label">Confidence Information</span>
          <span className="confidence-status">Not Available</span>
        </div>
      </div>
    );
  }

  const handleTriggerHITL = async () => {
    if (!onTriggerHITL) return;
    
    setIsTriggering(true);
    try {
      await onTriggerHITL(document.id, confidenceThreshold);
    } catch (error) {
      console.error('Error triggering HITL:', error);
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div className="confidence-display pattern1-confidence">
      <div className="confidence-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="confidence-main">
          <span className="confidence-label">Overall Confidence</span>
          <span 
            className={`confidence-score ${confidenceInfo.confidenceLevel}`}
            style={{ color: confidenceInfo.textColor }}
          >
            {formatConfidenceScore(confidenceInfo.overallConfidence)}
          </span>
        </div>
        
        <div className="confidence-indicators">
          {confidenceInfo.hitlTriggered && (
            <span className="hitl-indicator triggered">A2I Review Triggered</span>
          )}
          {!confidenceInfo.isAboveThreshold && (
            <span className="threshold-indicator below">Below Threshold</span>
          )}
          <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
        </div>
      </div>

      {isExpanded && (
        <div className="confidence-details">
          <div className="threshold-info">
            <span>Threshold: {formatConfidenceScore(confidenceThreshold)}</span>
          </div>
          
          {confidenceSummary.details.map((detail, index) => (
            <div key={index} className="confidence-detail-item">
              <span className="detail-label">{detail.label}</span>
              <span 
                className={`detail-score ${detail.isAboveThreshold ? 'above' : 'below'}`}
                style={{ color: detail.color }}
              >
                {formatConfidenceScore(detail.confidence)}
              </span>
            </div>
          ))}
          
          {!confidenceInfo.hitlTriggered && !confidenceInfo.isAboveThreshold && (
            <div className="hitl-actions">
              <button 
                className="trigger-hitl-btn"
                onClick={handleTriggerHITL}
                disabled={isTriggering}
              >
                {isTriggering ? 'Triggering A2I Review...' : 'Trigger A2I Human Review'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Pattern1ConfidenceDisplay;
