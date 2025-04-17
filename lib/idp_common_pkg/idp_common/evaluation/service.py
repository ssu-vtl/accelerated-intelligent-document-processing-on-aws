"""
Evaluation service for document extraction results.

This module provides a service for evaluating the extraction results of a document
by comparing them against expected values.
"""

import json
import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from idp_common import s3, utils, bedrock
from idp_common.models import Document, Section, Status
from idp_common.evaluation.models import (
    EvaluationMethod,
    EvaluationAttribute,
    AttributeEvaluationResult,
    SectionEvaluationResult,
    DocumentEvaluationResult
)
from idp_common.evaluation.comparator import compare_values
from idp_common.evaluation.metrics import calculate_metrics

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating document extraction results."""

    def __init__(
        self,
        region: str = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the evaluation service.
        
        Args:
            region: AWS region
            config: Configuration dictionary containing evaluation settings
        """
        self.config = config or {}
        self.region = region or self.config.get("region") or os.environ.get("AWS_REGION")
        
        # Set default LLM evaluation settings
        self.llm_config = self.config.get("evaluation", {}).get("llm_method", {})
        self.default_model = self.llm_config.get("model", "anthropic.claude-3-sonnet-20240229-v1:0")
        self.default_temperature = self.llm_config.get("temperature", 0.0)
        self.default_top_k = self.llm_config.get("top_k", 250)
        self.default_system_prompt = self.llm_config.get("system_prompt", 
            """You are an evaluator that helps determine if the predicted and expected values match for document attribute extraction. You will consider the context and meaning rather than just exact string matching.""")
        
        self.default_task_prompt = self.llm_config.get("task_prompt", 
            """I need to evaluate attribute extraction for a document of class: {DOCUMENT_CLASS}.

For the attribute named "{ATTRIBUTE_NAME}" described as "{ATTRIBUTE_DESCRIPTION}":
- Expected value: {EXPECTED_VALUE}
- Actual value: {ACTUAL_VALUE}

Do these values match in meaning, taking into account formatting differences, word order, abbreviations, and semantic equivalence?
Provide your assessment as a JSON with three fields:
- "match": boolean (true if they match, false if not)
- "score": number between 0 and 1 representing the confidence/similarity score
- "reason": brief explanation of your decision

Respond ONLY with the JSON and nothing else.
            """)
            
        logger.info("Initialized evaluation service with LLM configuration")
    
    def _get_attributes_for_class(self, class_name: str) -> List[EvaluationAttribute]:
        """
        Get attribute configurations for a document class.
        
        Args:
            class_name: Document class name
            
        Returns:
            List of attribute configurations
        """
        classes_config = self.config.get("classes", [])
        for class_config in classes_config:
            if class_config.get("name", "").lower() == class_name.lower():
                attributes = []
                for attr_config in class_config.get("attributes", []):
                    eval_method = EvaluationMethod.LLM  # Default method
                    threshold = 0.8  # Default evaluation threshold
                    
                    # Get evaluation method if specified in config
                    method_str = attr_config.get("evaluation_method", "LLM")
                    try:
                        eval_method = EvaluationMethod(method_str.upper())
                    except ValueError:
                        logger.warning(f"Unknown evaluation method: {method_str}, using LLM")
                    
                    # Get threshold if applicable
                    if "evaluation_threshold" in attr_config:
                        threshold = float(attr_config["evaluation_threshold"])
                    
                    attributes.append(EvaluationAttribute(
                        name=attr_config.get("name", ""),
                        description=attr_config.get("description", ""),
                        evaluation_method=eval_method,
                        evaluation_threshold=threshold
                    ))
                return attributes
        
        # Return empty list if class not found
        logger.warning(f"No attribute configuration found for class: {class_name}")
        return []
    
    def _load_extraction_results(self, uri: str) -> Dict[str, Any]:
        """
        Load extraction results from S3.
        
        Args:
            uri: S3 URI to the extraction results
            
        Returns:
            Extraction results as dictionary
        """
        try:
            content = s3.get_json_content(uri)
            
            # Check if results are wrapped in inference_result key
            if isinstance(content, dict) and "inference_result" in content:
                return content["inference_result"]
            return content
        except Exception as e:
            logger.error(f"Error loading extraction results from {uri}: {str(e)}")
            return {}
            
    
    def _count_classifications(
        self, 
        attr_name: str, 
        expected: Any, 
        actual: Any, 
        evaluation_method: EvaluationMethod,
        threshold: float,
        document_class: str = None,
        attr_description: str = None
    ) -> Tuple[int, int, int, int, int, int, float, Optional[str]]:
        """
        Count true/false positives/negatives for an attribute.
        
        Args:
            attr_name: Attribute name
            expected: Expected value
            actual: Actual value
            evaluation_method: Method to use for comparison
            threshold: Evaluation threshold for fuzzy methods
            document_class: Document class for LLM evaluation
            attr_description: Attribute description for LLM evaluation
            
        Returns:
            Tuple of (tn, fp, fn, tp, fp1, fp2, score, reason)
        """
        # Initialize counters
        tn = fp = fn = tp = fp1 = fp2 = 0
        score = 0.0
        reason = None
        
        # Case 1: Expected value is None/empty
        if expected is None or (isinstance(expected, str) and not expected.strip()):
            if actual is None or (isinstance(actual, str) and not actual.strip()):
                tn = 1  # Correctly didn't predict a value
                score = 1.0
            else:
                fp = fp1 = 1  # Incorrectly predicted a value when none expected
                score = 0.0
        
        # Case 2: Expected value exists but actual doesn't
        elif actual is None or (isinstance(actual, str) and not actual.strip()):
            fn = 1  # Missing prediction (false negative)
            score = 0.0
        
        # Case 3: Both values exist, compare them
        else:
            # Prepare LLM config if needed
            llm_config = None
            if evaluation_method == EvaluationMethod.LLM:
                llm_config = {
                    "model": self.default_model,
                    "temperature": self.default_temperature,
                    "top_k": self.default_top_k,
                    "system_prompt": self.default_system_prompt,
                    "task_prompt": self.default_task_prompt
                }
            
            # Use compare_values for all evaluation methods
            matched, score, reason = compare_values(
                expected=expected,
                actual=actual,
                method=evaluation_method,
                threshold=threshold,
                document_class=document_class,
                attr_name=attr_name,
                attr_description=attr_description,
                llm_config=llm_config
            )
                
            if matched:
                tp = 1  # Correct prediction
            else:
                fp = fp2 = 1  # Incorrect prediction
        
        return tn, fp, fn, tp, fp1, fp2, score, reason
    
    def evaluate_section(
        self, 
        section: Section,
        expected_results: Dict[str, Any],
        actual_results: Dict[str, Any]
    ) -> SectionEvaluationResult:
        """
        Evaluate extraction results for a document section.
        
        Args:
            section: Document section
            expected_results: Expected extraction results
            actual_results: Actual extraction results
            
        Returns:
            Evaluation results for the section
        """
        class_name = section.classification
        attributes = self._get_attributes_for_class(class_name)
        logger.debug(f"Evaluating Section {section.section_id} - class: {class_name}, content: {section}")
        
        # Evaluation counters
        tp = fp = fn = tn = fp1 = fp2 = 0
        attribute_results = []
        
        # Evaluate each attribute
        for attr_config in attributes:
            attr_name = attr_config.name
            expected_value = expected_results.get(attr_name)
            actual_value = actual_results.get(attr_name)
            
            # Count classifications
            attr_tn, attr_fp, attr_fn, attr_tp, attr_fp1, attr_fp2, score, reason = self._count_classifications(
                attr_name=attr_name,
                expected=expected_value,
                actual=actual_value,
                evaluation_method=attr_config.evaluation_method,
                threshold=attr_config.evaluation_threshold,
                document_class=class_name,
                attr_description=attr_config.description
            )
            
            # Update counters
            tn += attr_tn
            fp += attr_fp
            fn += attr_fn
            tp += attr_tp
            fp1 += attr_fp1
            fp2 += attr_fp2
            
            # Create attribute result - use the matched flag based on the true positive count
            matched = attr_tp > 0
            
            # Add evaluation method and evaluation threshold to the result
            attribute_results.append(AttributeEvaluationResult(
                name=attr_name,
                expected=expected_value,
                actual=actual_value,
                matched=matched,
                score=score,
                reason=reason,
                evaluation_method=attr_config.evaluation_method.value,
                evaluation_threshold=attr_config.evaluation_threshold if attr_config.evaluation_method in [EvaluationMethod.FUZZY, EvaluationMethod.BERT] else None
            ))
        
        # Calculate metrics
        metrics = calculate_metrics(tp=tp, fp=fp, fn=fn, tn=tn, fp1=fp1, fp2=fp2)
        
        return SectionEvaluationResult(
            section_id=section.section_id,
            document_class=class_name,
            attributes=attribute_results,
            metrics=metrics
        )
    
    def evaluate_document(
        self, 
        actual_document: Document, 
        expected_document: Document,
        store_results: bool = True
    ) -> Document:
        """
        Evaluate extraction results for an entire document and store results in S3.
        
        Args:
            actual_document: Document with actual extraction results
            expected_document: Document with expected extraction results
            store_results: Whether to store results in S3 (default: True)
            
        Returns:
            Updated actual document with evaluation results
        """
        try:
            # Start timing
            start_time = time.time()
            section_results = []
            
            # Track overall metrics
            total_tp = total_fp = total_fn = total_tn = total_fp1 = total_fp2 = 0
            
            # Process each section in the actual document
            for actual_section in actual_document.sections:
                section_id = actual_section.section_id
                
                # Find corresponding section in expected document
                expected_section = next(
                    (s for s in expected_document.sections if s.section_id == section_id),
                    None
                )
                
                if not expected_section:
                    logger.warning(f"No matching section found for section_id: {section_id}")
                    continue
                
                # Load extraction results
                actual_uri = actual_section.extraction_result_uri
                expected_uri = expected_section.extraction_result_uri
                
                if not actual_uri or not expected_uri:
                    logger.warning(f"Missing extraction URI for section: {section_id}")
                    continue
                
                actual_results = self._load_extraction_results(actual_uri)
                expected_results = self._load_extraction_results(expected_uri)
                
                # Evaluate section
                section_result = self.evaluate_section(
                    section=actual_section,
                    expected_results=expected_results,
                    actual_results=actual_results
                )
                
                # Collect raw counts from section for accurate overall metrics
                # Count matches and mismatches in the attributes
                for attr in section_result.attributes:
                    if attr.matched:
                        total_tp += 1
                    else:
                        # Handle different error cases
                        if attr.expected is None or (isinstance(attr.expected, str) and not attr.expected.strip()):
                            if attr.actual is None or (isinstance(attr.actual, str) and not attr.actual.strip()):
                                total_tn += 1  # Both empty/None
                            else:
                                total_fp += 1  # Expected None, got value
                                total_fp1 += 1
                        elif attr.actual is None or (isinstance(attr.actual, str) and not attr.actual.strip()):
                            total_fn += 1  # Expected value, got None
                        else:
                            total_fp += 1  # Both have values but don't match
                            total_fp2 += 1
                
                section_results.append(section_result)
            
            # Calculate overall metrics
            overall_metrics = calculate_metrics(
                tp=total_tp, 
                fp=total_fp, 
                fn=total_fn, 
                tn=total_tn, 
                fp1=total_fp1, 
                fp2=total_fp2
            )
            
            execution_time = time.time() - start_time
            
            # Create evaluation result
            evaluation_result = DocumentEvaluationResult(
                document_id=actual_document.id,
                section_results=section_results,
                overall_metrics=overall_metrics,
                execution_time=execution_time
            )
            
            # Store results if requested
            if store_results:
                # Generate output path
                output_bucket = actual_document.output_bucket
                output_key = f"{actual_document.input_key}/evaluation/results.json"
                
                # Store evaluation results in S3
                result_dict = evaluation_result.to_dict()
                s3.write_content(
                    content=result_dict,
                    bucket=output_bucket,
                    key=output_key,
                    content_type="application/json"
                )
                
                # Generate Markdown report
                markdown_report = evaluation_result.to_markdown()
                report_key = f"{actual_document.input_key}/evaluation/report.md"
                s3.write_content(
                    content=markdown_report,
                    bucket=output_bucket,
                    key=report_key,
                    content_type="text/markdown"
                )
                
                # Update document with evaluation report URI
                actual_document.evaluation_report_uri = f"s3://{output_bucket}/{report_key}"
                actual_document.status = Status.EVALUATED
                
                logger.info(f"Evaluation complete for document {actual_document.id}")
            
            # Attach evaluation result to document for immediate use
            actual_document.evaluation_result = evaluation_result
            
            return actual_document
                
        except Exception as e:
            logger.error(f"Error evaluating document: {str(e)}")
            actual_document.errors.append(f"Evaluation error: {str(e)}")
            return actual_document