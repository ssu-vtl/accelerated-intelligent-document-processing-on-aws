"""
Models for document evaluation.

This module provides data models for evaluation results and comparison methods.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


class EvaluationMethod(Enum):
    """Evaluation method types for different field comparison approaches."""
    EXACT = "EXACT"               # Exact string match after stripping punctuation and whitespace
    NUMERIC_EXACT = "NUMERIC_EXACT"  # Exact numeric match after normalizing
    BERT = "BERT"                 # Semantic similarity comparison using BERT
    HUNGARIAN = "HUNGARIAN"       # Bipartite matching for lists of values
    FUZZY = "FUZZY"               # Fuzzy string matching


@dataclass
class EvaluationAttribute:
    """Configuration for a single attribute to be evaluated."""
    name: str
    description: str
    evaluation_method: EvaluationMethod = EvaluationMethod.EXACT
    threshold: float = 0.0  # Used for BERT and FUZZY methods


@dataclass
class AttributeEvaluationResult:
    """Result of evaluation for a single attribute."""
    name: str
    expected: Any
    actual: Any
    matched: bool
    score: float = 1.0  # Score between 0 and 1 for fuzzy matching methods
    error_details: Optional[str] = None


@dataclass
class SectionEvaluationResult:
    """Result of evaluation for a document section."""
    section_id: str
    document_class: str
    attributes: List[AttributeEvaluationResult]
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def get_attribute_results(self) -> Dict[str, AttributeEvaluationResult]:
        """Get results indexed by attribute name."""
        return {attr.name: attr for attr in self.attributes}


@dataclass
class DocumentEvaluationResult:
    """Comprehensive evaluation result for a document."""
    document_id: str
    section_results: List[SectionEvaluationResult]
    overall_metrics: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    output_uri: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "overall_metrics": self.overall_metrics,
            "execution_time": self.execution_time,
            "output_uri": self.output_uri,
            "section_results": [
                {
                    "section_id": sr.section_id,
                    "document_class": sr.document_class,
                    "metrics": sr.metrics,
                    "attributes": [
                        {
                            "name": ar.name,
                            "expected": ar.expected,
                            "actual": ar.actual,
                            "matched": ar.matched,
                            "score": ar.score,
                            "error_details": ar.error_details
                        }
                        for ar in sr.attributes
                    ]
                }
                for sr in self.section_results
            ]
        }
    
    def to_markdown(self) -> str:
        """Convert evaluation results to markdown format."""
        sections = []
        
        # Add document overview
        sections.append(f"# Document Evaluation: {self.document_id}")
        sections.append("")
        
        # Add overall metrics
        sections.append("## Overall Metrics")
        metrics_table = "| Metric | Value |\n| ------ | ----- |\n"
        for metric, value in self.overall_metrics.items():
            metrics_table += f"| {metric} | {value:.4f} |\n"
        sections.append(metrics_table)
        sections.append("")
        
        # Add section results
        for sr in self.section_results:
            sections.append(f"## Section: {sr.section_id} ({sr.document_class})")
            
            # Section metrics
            sections.append("### Metrics")
            metrics_table = "| Metric | Value |\n| ------ | ----- |\n"
            for metric, value in sr.metrics.items():
                metrics_table += f"| {metric} | {value:.4f} |\n"
            sections.append(metrics_table)
            sections.append("")
            
            # Attribute results
            sections.append("### Attributes")
            attr_table = "| Attribute | Expected | Actual | Matched | Score |\n"
            attr_table += "| --------- | -------- | ------ | ------- | ----- |\n"
            for ar in sr.attributes:
                expected = str(ar.expected).replace("\n", " ")[:50]
                actual = str(ar.actual).replace("\n", " ")[:50]
                attr_table += f"| {ar.name} | {expected} | {actual} | {ar.matched} | {ar.score:.2f} |\n"
            sections.append(attr_table)
            sections.append("")
        
        # Add execution time
        sections.append(f"Execution time: {self.execution_time:.2f} seconds")
        
        return "\n".join(sections)