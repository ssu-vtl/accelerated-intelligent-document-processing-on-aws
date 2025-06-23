# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Models for criteria validation using LLMs.

This module provides data models for validation inputs and results.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class BedrockInput(BaseModel):
    """Input model for Bedrock LLM criteria validation."""

    question: str = Field(..., example="criteria that need to be evaluated.")
    prompt: str = Field(..., example="Evaluate the key points from the user history.")
    system_prompt: str = Field(..., example="Assigning role to the LLM.")
    criteria_type: str = Field(..., example="criteria type")
    recommendation: str = Field(..., example="recommendation options")
    user_history: Optional[str] = Field(None, example="Patient user history as a context")
    txt_file_uri: Optional[str] = Field(None, example="user history file location")
    initial_response: Optional[List] = Field(None, example="Initial results for multiple user history files")

    class Config:
        from_attributes = True
        extra = 'forbid'


class LLMResponse(BaseModel):
    """Response model from LLM for criteria validation."""

    criteria_type: str = Field(..., example="Type of criteria being evaluated")
    source_file: List[str] = Field(None, example="List of source file paths")
    question: str = Field(..., example="Question being evaluated")
    Recommendation: str = Field(..., example="Pass, Fail, or Information Not Found")
    Reasoning: str = Field(..., example="Explanation for the recommendation")

    @field_validator('Recommendation')
    @classmethod
    def validate_recommendation(cls, v):
        valid_values = ['Pass', 'Fail', 'Information Not Found']
        v = v.strip()
        if v not in valid_values:
            raise ValueError(f"Recommendation must be one of {valid_values}")
        return v

    @field_validator('Reasoning')
    @classmethod
    def clean_reasoning(cls, v):
        if not v:
            return v
        
        # Remove line breaks and extra spaces
        v = ' '.join(v.split())
        
        # Remove or replace problematic characters
        v = re.sub(r'[^\x20-\x7E]', '', v)  # Remove non-printable characters
        
        # Remove markdown-style bullets and numbers
        v = re.sub(r'^\s*[-*•]\s*', '', v)
        v = re.sub(r'^\s*\d+\.\s*', '', v)
        
        return v

    @field_validator('source_file')
    @classmethod
    def validate_source_files(cls, v):
        if not v:
            return []
        # Ensure all files are s3:// URLs
        return [f if f.startswith('s3://') else f's3://{f}' for f in v]

    class Config:
        extra = "forbid"  # Prevent additional fields
        str_strip_whitespace = True  # Strip whitespace from strings


@dataclass
class CriteriaValidationResult:
    """Result of criteria validation for a document request."""

    request_id: str
    criteria_type: str
    validation_responses: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
    metering: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    output_uri: Optional[str] = None
    errors: Optional[List[str]] = None
    cost_tracking: Optional[Dict[str, Any]] = None
