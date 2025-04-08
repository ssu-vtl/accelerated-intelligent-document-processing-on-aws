"""
Data classes for OCR processing results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class OcrPageResult:
    """Results for a single page processed with OCR."""
    
    raw_text_uri: str
    """S3 URI for the raw Textract response."""
    
    parsed_text_uri: str
    """S3 URI for the parsed text content."""
    
    image_uri: str
    """S3 URI for the page image."""
    
    tables: List[Dict[str, Any]] = field(default_factory=list)
    """Optional table data extracted from the page."""
    
    forms: Dict[str, str] = field(default_factory=dict)
    """Optional form key-value pairs extracted from the page."""


@dataclass
class OcrDocumentResult:
    """Results for an entire document processed with OCR."""
    
    num_pages: int
    """Number of pages in the document."""
    
    pages: Dict[str, OcrPageResult]
    """Results for each page, keyed by page number (1-based)."""
    
    metering: Dict[str, Any]
    """Metering data for the processing."""
    
    input_bucket: str
    """S3 bucket containing the input document."""
    
    input_key: str
    """S3 key for the input document."""
    
    output_bucket: str
    """S3 bucket containing the OCR results."""
    
    output_prefix: str
    """S3 prefix for the OCR results."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for API responses."""
        return {
            "metadata": {
                "input_bucket": self.input_bucket,
                "object_key": self.input_key,
                "output_bucket": self.output_bucket,
                "output_prefix": self.output_prefix,
                "num_pages": self.num_pages,
                "metering": self.metering
            },
            "pages": {
                page_num: {
                    "rawTextUri": page_result.raw_text_uri,
                    "parsedTextUri": page_result.parsed_text_uri,
                    "imageUri": page_result.image_uri,
                    **({"tables": page_result.tables} if page_result.tables else {}),
                    **({"forms": page_result.forms} if page_result.forms else {})
                }
                for page_num, page_result in self.pages.items()
            }
        }