"""
OCR Service for document processing with AWS Textract.

This module provides a service for extracting text from PDF documents
using AWS Textract, with support for concurrent processing of multiple pages.
"""

import boto3
import concurrent.futures
import io
import json
import logging
import os
import time
from typing import Dict, List, Tuple, Any, Optional, BinaryIO
from botocore.config import Config


import fitz  # PyMuPDF

from idp_common import s3, utils
from idp_common.ocr.results import OcrPageResult, OcrDocumentResult

logger = logging.getLogger(__name__)


class OcrService:
    """Service for OCR processing of documents using AWS Textract."""

    def __init__(
        self,
        region: Optional[str] = None,
        max_workers: int = 20,
        enhanced_features: bool = False,
    ):
        """
        Initialize the OCR service.

        Args:
            region: AWS region for Textract service
            max_workers: Maximum number of concurrent workers for page processing
            enhanced_features: If True, uses document analysis with tables, forms
                               If False, uses basic text detection (faster)
        """
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.max_workers = max_workers
        self.enhanced_features = enhanced_features
        
        # Initialize Textract client with adaptive retries
        adaptive_config = Config(
            retries={'max_attempts': 100, 'mode': 'adaptive'},
            max_pool_connections=max_workers*3
        )
        self.textract_client = boto3.client(
            'textract', 
            region_name=self.region, 
            config=adaptive_config
        )

    def process_document(
        self, 
        pdf_content: bytes, 
        output_bucket: str, 
        prefix: str
    ) -> OcrDocumentResult:
        """
        Process a PDF document with OCR.

        Args:
            pdf_content: Binary content of the PDF document
            output_bucket: S3 bucket to store OCR results
            prefix: S3 prefix for storing OCR results

        Returns:
            OcrDocumentResult containing metadata and page results
        """
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        num_pages = len(pdf_document)
        page_results = {}
        metering = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(
                    self._process_single_page, 
                    i, 
                    pdf_document, 
                    output_bucket, 
                    prefix
                ): i 
                for i in range(num_pages)
            }
            
            for future in concurrent.futures.as_completed(future_to_page):
                page_index = future_to_page[future]
                try:
                    result, page_metering = future.result()
                    page_results[str(page_index + 1)] = result
                    # Merge metering data
                    metering = utils.merge_metering_data(metering, page_metering)
                except Exception as e:
                    logger.error(f"Error processing page {page_index + 1}: {str(e)}")
                    raise
        
        pdf_document.close()
        
        # Create and return result object
        return OcrDocumentResult(
            num_pages=num_pages,
            pages=page_results,
            metering=metering,
            input_bucket="",  # Will be set by caller
            input_key="",     # Will be set by caller
            output_bucket=output_bucket,
            output_prefix=prefix
        )

    def _process_single_page(
        self, 
        page_index: int, 
        pdf_document: fitz.Document, 
        output_bucket: str, 
        prefix: str
    ) -> Tuple[OcrPageResult, Dict[str, Any]]:
        """
        Process a single page of a PDF document.

        Args:
            page_index: Zero-based index of the page
            pdf_document: PyMuPDF document object
            output_bucket: S3 bucket to store results
            prefix: S3 prefix for storing results

        Returns:
            Tuple of (OcrPageResult, metering_data)
        """
        t0 = time.time()
        page_id = page_index + 1
        
        # Extract page image
        page = pdf_document.load_page(page_index)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("jpeg")
        
        # Upload image to S3
        image_key = f"{prefix}/pages/{page_id}/image.jpg"
        s3.write_content(
            img_bytes, 
            output_bucket, 
            image_key, 
            content_type='image/jpeg'
        )
        
        t1 = time.time()
        logger.info(f"Time for image conversion (page {page_id}): {t1-t0:.6f} seconds")
        
        # Process with Textract
        if self.enhanced_features:
            textract_result = self._analyze_document(img_bytes)
        else:
            textract_result = self.textract_client.detect_document_text(
                Document={"Bytes": img_bytes}
            )
        
        # Extract metering data
        metering = {
            f"textract/{self._get_api_name()}": {
                "pages": textract_result["DocumentMetadata"]["Pages"]
            }
        }
        
        # Store raw Textract response
        raw_text_key = f"{prefix}/pages/{page_id}/rawText.json"
        s3.write_content(
            textract_result, 
            output_bucket, 
            raw_text_key, 
            content_type='application/json'
        )
        
        # Parse and store text content
        parsed_text = self._parse_textract_response(textract_result)
        parsed_text_key = f"{prefix}/pages/{page_id}/result.json"
        s3.write_content(
            {"text": parsed_text}, 
            output_bucket, 
            parsed_text_key, 
            content_type='application/json'
        )
        
        t2 = time.time()
        logger.info(f"Time for Textract (page {page_id}): {t2-t1:.6f} seconds")
        
        # Create and return page result
        result = OcrPageResult(
            raw_text_uri=f"s3://{output_bucket}/{raw_text_key}",
            parsed_text_uri=f"s3://{output_bucket}/{parsed_text_key}",
            image_uri=f"s3://{output_bucket}/{image_key}"
        )
        
        return result, metering
    
    def _analyze_document(self, document_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze document using enhanced Textract features.

        Args:
            document_bytes: Binary content of the document image

        Returns:
            Textract API response
        """
        response = self.textract_client.analyze_document(
            Document={"Bytes": document_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )
        return response
    
    def _get_api_name(self) -> str:
        """Get the name of the Textract API being used."""
        return "analyze_document" if self.enhanced_features else "detect_document_text"
    
    def _parse_textract_response(self, response: Dict[str, Any]) -> str:
        """
        Parse Textract response into text.

        In future versions, this could be enhanced to extract tables, forms, etc.
        
        Args:
            response: Raw Textract API response

        Returns:
            Extracted text content
        """
        try:
            # When available, use textractor for parsing
            from textractor.parsers import response_parser
            return response_parser.parse(response).text
        except ImportError:
            # Fallback to simple text extraction
            text_lines = []
            for block in response.get("Blocks", []):
                if block.get("BlockType") == "LINE":
                    text_lines.append(block.get("Text", ""))
            return "\n".join(text_lines)