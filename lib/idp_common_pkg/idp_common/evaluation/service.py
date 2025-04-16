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
            """You are an evaluator that helps determine if the predicted and expected values match.
            Some examples of fields that can be in different formats are dates, addresses, and monetary amounts.
            When comparing values, consider both semantic meaning and normalized formats.
            
            Respond with one of these categories:
            TRUE POSITIVE: The fields have the same meaning, even if formats differ (e.g., 2023-05-15 and 2023/05/15).
            FALSE POSITIVE: The expected field is None and the predicted field is populated, or the fields have different meanings.
            TRUE NEGATIVE: Both the expected field and predicted field are None or empty.
            FALSE NEGATIVE: The expected field is populated, but the predicted field is None or empty.
            
            Provide only the category (TRUE POSITIVE, FALSE POSITIVE, TRUE NEGATIVE, or FALSE NEGATIVE) and nothing else.
            """)
        
        self.default_task_prompt = self.llm_config.get("task_prompt", 
            """I need to evaluate attribute extraction for a document of class: {DOCUMENT_CLASS}
            
            Attribute: {ATTRIBUTE_NAME_AND_DESCRIPTION}
            
            Expected value:
            {EXPECTED_VALUE}
            
            Predicted value:
            {PREDICTED_VALUE}
            
            Does the predicted value match the expected value? Consider both the exact and semantic meaning.
            Respond with only one of: TRUE POSITIVE, FALSE POSITIVE, TRUE NEGATIVE, or FALSE NEGATIVE.
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
                    method_str = attr_config.get("evaluation_method", "EXACT")
                    try:
                        eval_method = EvaluationMethod(method_str.upper())
                    except ValueError:
                        logger.warning(f"Unknown evaluation method: {method_str}, using EXACT")
                    
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
            
    def _evaluate_with_llm(
        self,
        document_class: str,
        attr_name: str,
        attr_description: str,
        expected: Any,
        actual: Any
    ) -> Tuple[bool, float]:
        """
        Evaluate attribute using LLM.
        
        Args:
            document_class: Document class name
            attr_name: Attribute name
            attr_description: Attribute description
            expected: Expected value
            actual: Actual value
            
        Returns:
            Tuple of (matched, score)
        """
        try:
            # Format attribute description
            attr_name_and_description = f"{attr_name}" 
            if attr_description:
                attr_name_and_description += f" - {attr_description}"
            
            logger.debug(f"LLM evaluation starting for attribute: {attr_name}")
            logger.debug(f"Document class: {document_class}")
            logger.debug(f"Attribute description: {attr_description}")
                
            # Handle None values
            expected_str = str(expected) if expected is not None else "None"
            actual_str = str(actual) if actual is not None else "None"
            
            logger.debug(f"Expected value: {expected_str}")
            logger.debug(f"Actual value: {actual_str}")
            
            # Check if we're using the updated task prompt format or the older one
            task_placeholders = {
                "DOCUMENT_CLASS": document_class,
                "ATTRIBUTE_NAME": attr_name,
                "ATTRIBUTE_DESCRIPTION": attr_description,
                "EXPECTED_VALUE": expected_str,
                "ACTUAL_VALUE": actual_str,
                # Also support the old format
                "ATTRIBUTE_NAME_AND_DESCRIPTION": attr_name_and_description,
                "PREDICTED_VALUE": actual_str
            }
            
            # Format task prompt with placeholders
            try:
                logger.debug(f"Raw task prompt template: {self.default_task_prompt}")
                # Try to identify which placeholders are used in the prompt
                placeholders_used = []
                for placeholder in task_placeholders.keys():
                    if "{" + placeholder + "}" in self.default_task_prompt:
                        placeholders_used.append(placeholder)
                
                logger.debug(f"Placeholders found in prompt: {placeholders_used}")
                
                # Format the prompt with detected placeholders
                task_prompt = self.default_task_prompt.format(**task_placeholders)
                logger.debug(f"Formatted task prompt: {task_prompt}")
            except KeyError as e:
                logger.error(f"Task prompt formatting error - missing placeholder: {e}")
                # Try with a simpler format as fallback
                task_prompt = f"""Document class: {document_class}
                Attribute: {attr_name} - {attr_description}
                Expected: {expected_str}
                Actual: {actual_str}
                Do these values match?"""
                logger.debug(f"Using fallback prompt: {task_prompt}")
            except Exception as e:
                logger.error(f"Task prompt formatting error: {str(e)}")
                raise
            
            # Create content for LLM request
            content = [{"text": task_prompt}]
            
            # Log system prompt for debugging
            logger.debug(f"System prompt: {self.default_system_prompt}")
            logger.debug(f"Model: {self.default_model}")
            
            # Call Bedrock model
            logger.debug("Calling Bedrock model")
            response = bedrock.invoke_model(
                model_id=self.default_model,
                system_prompt=self.default_system_prompt,
                content=content,
                temperature=self.default_temperature,
                top_k=self.default_top_k
            )
            
            # Extract response text
            result_text = bedrock.extract_text_from_response(response).strip()
            logger.debug(f"Raw LLM response: {result_text}")
            
            # Try to parse as JSON first (new format)
            try:
                result_json = json.loads(result_text)
                logger.debug(f"Parsed JSON response: {result_json}")
                
                # Extract values from JSON
                if isinstance(result_json, dict):
                    match_value = result_json.get("match", False)
                    score_value = result_json.get("score", 0.0)
                    reason = result_json.get("reason", "No reason provided")
                    
                    logger.info(f"LLM evaluation for {attr_name}: match={match_value}, score={score_value}, reason={reason}")
                    return bool(match_value), float(score_value)
            except Exception as e:
                logger.error(f"Error parsing LLM response: {str(e)}")
                logger.error(f"Raw response was: {result_text}")
                logger.error(f'Response from LLM must be JSON like: {"match": boolean, "score": score, "reason": reason"}')
                matched, score = False, 0.0
                return matched, score
            
        except Exception as e:
            logger.error(f"Error in LLM evaluation for {attr_name}: {str(e)}", exc_info=True)
            # Fall back to exact comparison on failure
            return compare_values(expected, actual, EvaluationMethod.EXACT)
    
    def _count_classifications(
        self, 
        attr_name: str, 
        expected: Any, 
        actual: Any, 
        evaluation_method: EvaluationMethod,
        threshold: float  # Will keep this as threshold for backward compatibility
    ) -> Tuple[int, int, int, int, int, int]:
        """
        Count true/false positives/negatives for an attribute.
        
        Args:
            attr_name: Attribute name
            expected: Expected value
            actual: Actual value
            evaluation_method: Method to use for comparison
            threshold: Evaluation threshold for fuzzy methods
            
        Returns:
            Tuple of (tn, fp, fn, tp, fp1, fp2)
        """
        # Initialize counters
        tn = fp = fn = tp = fp1 = fp2 = 0
        
        # Case 1: Expected value is None/empty
        if expected is None or (isinstance(expected, str) and not expected.strip()):
            if actual is None or (isinstance(actual, str) and not actual.strip()):
                tn = 1  # Correctly didn't predict a value
            else:
                fp = fp1 = 1  # Incorrectly predicted a value when none expected
        
        # Case 2: Expected value exists but actual doesn't
        elif actual is None or (isinstance(actual, str) and not actual.strip()):
            fn = 1  # Missing prediction (false negative)
        
        # Case 3: Both values exist, compare them
        else:
            if evaluation_method == EvaluationMethod.LLM:
                matched, score = self._evaluate_with_llm(
                    document_class="unknown",  # We don't have the class name at this point
                    attr_name=attr_name,
                    attr_description="",
                    expected=expected,
                    actual=actual
                )
            else:
                matched, score = compare_values(expected, actual, evaluation_method, threshold)
            if matched:
                tp = 1  # Correct prediction
            else:
                fp = fp2 = 1  # Incorrect prediction
        
        return tn, fp, fn, tp, fp1, fp2
    
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
        
        # Evaluation counters
        tp = fp = fn = tn = fp1 = fp2 = 0
        attribute_results = []
        
        # Evaluate each attribute
        for attr_config in attributes:
            attr_name = attr_config.name
            expected_value = expected_results.get(attr_name)
            actual_value = actual_results.get(attr_name)
            
            # Count classifications
            attr_tn, attr_fp, attr_fn, attr_tp, attr_fp1, attr_fp2 = self._count_classifications(
                attr_name=attr_name,
                expected=expected_value,
                actual=actual_value,
                evaluation_method=attr_config.evaluation_method,
                threshold=attr_config.evaluation_threshold
            )
            
            # Update counters
            tn += attr_tn
            fp += attr_fp
            fn += attr_fn
            tp += attr_tp
            fp1 += attr_fp1
            fp2 += attr_fp2
            
            # Create attribute result
            matched = attr_tp > 0
            # Get score from comparison
            if attr_config.evaluation_method == EvaluationMethod.LLM:
                matched, score = self._evaluate_with_llm(
                    document_class=class_name,
                    attr_name=attr_name,
                    attr_description=attr_config.description,
                    expected=expected_value,
                    actual=actual_value
                )
            else:
                _, score = compare_values(
                    expected=expected_value,
                    actual=actual_value,
                    method=attr_config.evaluation_method,
                    threshold=attr_config.evaluation_threshold
                )
            
            # Add evaluation method and evaluation threshold to the result
            attribute_results.append(AttributeEvaluationResult(
                name=attr_name,
                expected=expected_value,
                actual=actual_value,
                matched=matched,
                score=score,
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
                
                # Update overall counters from section metrics
                section_metrics = section_result.metrics
                precision = section_metrics.get("precision", 0)
                recall = section_metrics.get("recall", 0)
                
                # Estimate TP, FP, FN from precision and recall
                # (These are approximations as we don't have the raw counts)
                if precision > 0 and recall > 0:
                    # These formulas are derived from:
                    # precision = tp / (tp + fp)
                    # recall = tp / (tp + fn)
                    # We solve for tp, fp, fn
                    section_tp = 1
                    section_fp = section_tp * (1 - precision) / precision if precision > 0 else 0
                    section_fn = section_tp * (1 - recall) / recall if recall > 0 else 0
                    
                    total_tp += section_tp
                    total_fp += section_fp
                    total_fn += section_fn
                
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
    