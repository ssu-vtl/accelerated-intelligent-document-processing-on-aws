"""
Models for document summarization.

This module provides data models for document summarization results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class DocumentSummary:
    """Model for document summary results."""
    
    brief_summary: str
    """A brief 1-2 sentence overview of the document."""
    
    detailed_summary: str
    """A comprehensive summary with key points organized by sections."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Optional metadata about the summarization process."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'brief_summary': self.brief_summary,
            'detailed_summary': self.detailed_summary,
            'metadata': self.metadata
        }
