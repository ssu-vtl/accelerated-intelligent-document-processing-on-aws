// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * Service for handling HITL A2I (Human In The Loop with Amazon Augmented AI) operations
 */

const API_BASE_URL = process.env.REACT_APP_HITL_API_URL || '/api';

/**
 * Trigger HITL for a document
 * @param {string} documentId - Document ID
 * @param {number} confidenceThreshold - Confidence threshold
 * @param {boolean} forceHitl - Force HITL even if confidence is above threshold
 * @returns {Promise<Object>} HITL trigger response
 */
export const triggerHITL = async (documentId, confidenceThreshold = 0.8, forceHitl = false) => {
  try {
    const response = await fetch(`${API_BASE_URL}/trigger-hitl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        confidence_threshold: confidenceThreshold,
        force_hitl: forceHitl
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error triggering HITL:', error);
    throw error;
  }
};

/**
 * Get HITL status for a document
 * @param {string} documentId - Document ID
 * @returns {Promise<Object>} HITL status response
 */
export const getHITLStatus = async (documentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/hitl-status/${documentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting HITL status:', error);
    throw error;
  }
};

/**
 * Update confidence threshold for a document
 * @param {string} documentId - Document ID
 * @param {number} newThreshold - New confidence threshold
 * @returns {Promise<Object>} Update response
 */
export const updateConfidenceThreshold = async (documentId, newThreshold) => {
  try {
    const response = await fetch(`${API_BASE_URL}/update-threshold`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        confidence_threshold: newThreshold
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating confidence threshold:', error);
    throw error;
  }
};

/**
 * Get confidence analysis for a document
 * @param {string} documentId - Document ID
 * @param {number} threshold - Confidence threshold to analyze against
 * @returns {Promise<Object>} Confidence analysis response
 */
export const getConfidenceAnalysis = async (documentId, threshold = 0.8) => {
  try {
    const response = await fetch(`${API_BASE_URL}/confidence-analysis/${documentId}?threshold=${threshold}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting confidence analysis:', error);
    throw error;
  }
};
