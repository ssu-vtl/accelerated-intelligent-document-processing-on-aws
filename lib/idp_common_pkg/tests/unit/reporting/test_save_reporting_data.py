# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Unit tests for the SaveReportingData class.
"""

from unittest.mock import MagicMock, patch

import pytest
from idp_common.models import Document
from idp_common.reporting.save_reporting_data import SaveReportingData


@pytest.mark.unit
class TestSaveReportingData:
    """Test cases for SaveReportingData class."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        with patch("boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            yield mock_s3

    @pytest.fixture
    def document_with_evaluation_uri(self):
        """Create a test document with evaluation results URI."""
        doc = Document(id="test-doc-123", input_key="test/document.pdf")
        doc.evaluation_results_uri = (
            "s3://test-bucket/test/document.pdf/evaluation/results.json"
        )
        return doc

    @pytest.fixture
    def document_without_evaluation_uri(self):
        """Create a test document without evaluation results URI."""
        return Document(id="test-doc-456", input_key="test/document2.pdf")

    @pytest.fixture
    def mock_evaluation_results(self):
        """Create mock evaluation results."""
        return {
            "overall_metrics": {
                "accuracy": 0.85,
                "precision": 0.9,
                "recall": 0.8,
                "f1_score": 0.85,
                "false_alarm_rate": 0.1,
                "false_discovery_rate": 0.1,
            },
            "execution_time": 1.5,
            "section_results": [
                {
                    "section_id": "section-1",
                    "document_class": "invoice",
                    "metrics": {
                        "accuracy": 0.9,
                        "precision": 0.95,
                        "recall": 0.85,
                        "f1_score": 0.9,
                        "false_alarm_rate": 0.05,
                        "false_discovery_rate": 0.05,
                    },
                    "attributes": [
                        {
                            "name": "invoice_number",
                            "expected": "INV-123",
                            "actual": "INV-123",
                            "matched": True,
                            "score": 1.0,
                            "reason": "Exact match",
                            "evaluation_method": "exact",
                            "confidence": "high",
                        }
                    ],
                }
            ],
        }

    def test_serialize_value(self):
        """Test the _serialize_value method."""
        reporter = SaveReportingData("test-bucket")

        # Test various types
        assert reporter._serialize_value(None) is None
        assert reporter._serialize_value("test") == "test"
        assert reporter._serialize_value(123) == "123"
        assert reporter._serialize_value(True) == "True"
        assert reporter._serialize_value({"key": "value"}) == '{"key": "value"}'
        assert reporter._serialize_value(["item1", "item2"]) == '["item1", "item2"]'

    def test_parse_s3_uri(self):
        """Test the _parse_s3_uri method."""
        reporter = SaveReportingData("test-bucket")

        # Test valid S3 URI
        bucket, key = reporter._parse_s3_uri("s3://test-bucket/path/to/file.json")
        assert bucket == "test-bucket"
        assert key == "path/to/file.json"

        # Test S3 URI with leading slash in key
        bucket, key = reporter._parse_s3_uri("s3://test-bucket//path/to/file.json")
        assert bucket == "test-bucket"
        assert key == "path/to/file.json"

        # Test invalid S3 URI
        with pytest.raises(ValueError):
            reporter._parse_s3_uri("http://test-bucket/path/to/file.json")

    def test_save_with_empty_data_to_save(
        self, mock_s3_client, document_with_evaluation_uri
    ):
        """Test the save method with empty data_to_save list."""
        reporter = SaveReportingData("test-bucket")

        results = reporter.save(document_with_evaluation_uri, [])

        assert results == []

    @patch.object(SaveReportingData, "save_evaluation_results")
    def test_save_with_evaluation_results(
        self, mock_save_eval, mock_s3_client, document_with_evaluation_uri
    ):
        """Test the save method with evaluation_results in data_to_save."""
        reporter = SaveReportingData("test-bucket")

        # Mock the save_evaluation_results method
        mock_save_eval.return_value = {"statusCode": 200, "body": "Success"}

        results = reporter.save(document_with_evaluation_uri, ["evaluation_results"])

        # Verify calls
        mock_save_eval.assert_called_once_with(document_with_evaluation_uri)
        assert results == [{"statusCode": 200, "body": "Success"}]

    def test_save_evaluation_results_no_uri(
        self, mock_s3_client, document_without_evaluation_uri
    ):
        """Test save_evaluation_results with a document that has no evaluation results URI."""
        reporter = SaveReportingData("test-bucket")

        result = reporter.save_evaluation_results(document_without_evaluation_uri)

        assert result is None
