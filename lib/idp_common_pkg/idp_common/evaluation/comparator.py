"""
Comparator module for document evaluation.

This module provides methods to compare expected and actual values using various comparison strategies.
"""

import re
import ast
from typing import Any, Tuple, List, Union, Optional
from munkres import Munkres, make_cost_matrix
import numpy as np

from idp_common.evaluation.models import EvaluationMethod


def strip_punctuation_space(text: str) -> str:
    """
    Strip punctuation and standardize whitespace in text.
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text with punctuation removed and whitespace standardized
    """
    if not isinstance(text, str):
        text = str(text)
    # Replace punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text


def normalize_numeric(value: Any) -> float:
    """
    Normalize a numeric value by removing currency symbols and commas.
    
    Args:
        value: Input value to normalize
        
    Returns:
        Normalized float value
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        value = str(value)
    
    # Remove currency symbols, commas, parentheses
    value = value.replace('$', '').replace(',', '').replace('(', '').replace(')', '')
    
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot convert {value} to numeric value")


def compare_exact(expected: Any, actual: Any) -> Tuple[bool, float]:
    """
    Compare values for exact string match.
    
    Args:
        expected: Expected value
        actual: Actual value
        
    Returns:
        Tuple of (matched, score)
    """
    if expected is None and actual is None:
        return True, 1.0
    
    if expected is None or actual is None:
        return False, 0.0
    
    expected_str = strip_punctuation_space(str(expected))
    actual_str = strip_punctuation_space(str(actual))
    
    return expected_str == actual_str, 1.0 if expected_str == actual_str else 0.0


def compare_numeric(expected: Any, actual: Any) -> Tuple[bool, float]:
    """
    Compare values for exact numeric match.
    
    Args:
        expected: Expected value
        actual: Actual value
        
    Returns:
        Tuple of (matched, score)
    """
    if expected is None and actual is None:
        return True, 1.0
    
    if expected is None or actual is None:
        return False, 0.0
    
    try:
        expected_num = normalize_numeric(expected)
        actual_num = normalize_numeric(actual)
        return expected_num == actual_num, 1.0 if expected_num == actual_num else 0.0
    except ValueError:
        # Fall back to exact string comparison if numeric conversion fails
        return compare_exact(expected, actual)


def convert_to_list(value: Any) -> List[str]:
    """
    Convert a value to a list.
    
    Args:
        value: Input value to convert (string, list, or other)
        
    Returns:
        List of strings
    """
    if value is None:
        return []
    
    # If already a list, return as is
    if isinstance(value, list):
        return [str(item) for item in value]
    
    # Try to convert a string representation of a list to a list
    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        try:
            parsed_list = ast.literal_eval(value)
            if isinstance(parsed_list, list):
                return [str(item) for item in parsed_list]
        except (ValueError, SyntaxError):
            pass
    
    # Default: treat as a single value
    return [str(value)]


def compare_hungarian(expected: Any, actual: Any) -> Tuple[int, int]:
    """
    Compare lists using Hungarian algorithm for maximum bipartite matching.
    
    Args:
        expected: Expected list or value
        actual: Actual list or value
        
    Returns:
        Tuple of (true_positives, false_positives)
    """
    expected_list = convert_to_list(expected)
    actual_list = convert_to_list(actual)
    
    # If comparing simple values (not lists), use exact matching
    if len(expected_list) == 1 and len(actual_list) == 1:
        expected_str = strip_punctuation_space(expected_list[0])
        actual_str = strip_punctuation_space(actual_list[0])
        return (1, 0) if expected_str == actual_str else (0, 1)
    
    # Empty lists edge case
    if not expected_list and not actual_list:
        return 0, 0
    if not expected_list:
        return 0, len(actual_list)
    if not actual_list:
        return 0, 0
    
    # Create cost matrix for Hungarian algorithm
    matrix = np.zeros((len(expected_list), len(actual_list)))
    
    # Fill matrix with comparison scores
    for i, exp_val in enumerate(expected_list):
        for j, act_val in enumerate(actual_list):
            # Try numeric comparison first, fall back to string comparison
            try:
                exp_num = normalize_numeric(exp_val)
                act_num = normalize_numeric(act_val)
                matrix[i, j] = 1.0 if exp_num == act_num else 0.0
            except ValueError:
                exp_str = strip_punctuation_space(exp_val)
                act_str = strip_punctuation_space(act_val)
                matrix[i, j] = 1.0 if exp_str == act_str else 0.0
    
    # Convert to cost matrix (Hungarian algorithm minimizes cost)
    cost_matrix = make_cost_matrix(matrix, lambda x: 1-x)
    
    # Compute the optimal assignment
    m = Munkres()
    indexes = m.compute(cost_matrix.tolist())
    
    # Count matches
    true_positives = sum(1 for i, j in indexes if matrix[i, j] > 0)
    false_positives = len(actual_list) - true_positives
    
    return true_positives, false_positives


def fuzz_score(s1: str, s2: str) -> float:
    """
    Calculate fuzzy match score between two strings.
    
    This is a simplified implementation. For a real implementation,
    you might want to use a dedicated library like python-Levenshtein or fuzzywuzzy.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Normalize inputs
    s1 = strip_punctuation_space(s1)
    s2 = strip_punctuation_space(s2)
    
    # Perfect match
    if s1 == s2:
        return 1.0
    
    # Edge cases
    if not s1 or not s2:
        return 0.0
    
    # Calculate Levenshtein distance (simplified implementation)
    len_s1, len_s2 = len(s1), len(s2)
    d = [[0 for _ in range(len_s2 + 1)] for _ in range(len_s1 + 1)]
    
    for i in range(len_s1 + 1):
        d[i][0] = i
    for j in range(len_s2 + 1):
        d[0][j] = j
    
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            d[i][j] = min(
                d[i-1][j] + 1,      # deletion
                d[i][j-1] + 1,      # insertion
                d[i-1][j-1] + cost  # substitution
            )
    
    # Convert to similarity score (1.0 for identical, approaching 0.0 for very different)
    max_len = max(len_s1, len_s2)
    return 1.0 - (d[len_s1][len_s2] / max_len if max_len > 0 else 0.0)


def compare_fuzzy(expected: Any, actual: Any, threshold: float = 0.8) -> Tuple[bool, float]:
    """
    Compare values using fuzzy string matching.
    
    Args:
        expected: Expected value
        actual: Actual value
        threshold: Minimum similarity score to consider a match (0.0 to 1.0)
        
    Returns:
        Tuple of (matched, score)
    """
    if expected is None and actual is None:
        return True, 1.0
    
    if expected is None or actual is None:
        return False, 0.0
    
    score = fuzz_score(str(expected), str(actual))
    return score >= threshold, score


def compare_values(
    expected: Any, 
    actual: Any, 
    method: EvaluationMethod, 
    threshold: float = 0.8
) -> Tuple[bool, float]:
    """
    Compare values using the specified method.
    
    Args:
        expected: Expected value
        actual: Actual value
        method: Comparison method to use
        threshold: Threshold for fuzzy/BERT methods
        
    Returns:
        Tuple of (matched, score)
    """
    if method == EvaluationMethod.EXACT:
        return compare_exact(expected, actual)
    
    elif method == EvaluationMethod.NUMERIC_EXACT:
        return compare_numeric(expected, actual)
    
    elif method == EvaluationMethod.FUZZY:
        return compare_fuzzy(expected, actual, threshold)
    
    elif method == EvaluationMethod.HUNGARIAN:
        tp, fp = compare_hungarian(expected, actual)
        # Convert Hungarian output to match/score format
        if tp + fp == 0:
            return True, 1.0  # Both lists empty
        matched = tp > 0 and fp == 0
        score = tp / (tp + fp) if tp + fp > 0 else 0.0
        return matched, score
    
    elif method == EvaluationMethod.BERT:
        # BERT comparison would require additional dependencies
        # For simplicity, we'll fall back to fuzzy matching
        return compare_fuzzy(expected, actual, threshold)
    
    else:
        # Default to exact matching
        return compare_exact(expected, actual)