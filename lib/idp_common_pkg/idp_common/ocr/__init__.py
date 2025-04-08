"""
OCR module for IDP Common Package.

Provides a service for processing PDF documents with AWS Textract.
"""

from idp_common.ocr.service import OcrService
from idp_common.ocr.results import OcrPageResult, OcrDocumentResult

__all__ = ['OcrService', 'OcrPageResult', 'OcrDocumentResult']