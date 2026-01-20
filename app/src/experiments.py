"""Experiment configurations and validators"""
from dataclasses import dataclass
from typing import Callable, Any, Dict
import re


@dataclass
class ExperimentConfig:
    """Configuration for a benchmark experiment"""
    name: str
    description: str
    build_context: Callable
    build_query: Callable
    build_expected: Callable
    validator: Callable


def validate_needle(output: str, payload: Any) -> tuple[bool, str]:
    """Validate needle-in-haystack experiments"""
    if payload.expected.lower() in output.lower():
        return True, "Found expected needle in output"
    return False, f"Expected needle '{payload.expected}' not found in output"


def validate_label_counts(output: str, payload: Any) -> tuple[bool, str]:
    """Validate label counting experiments"""
    expected: Dict[str, int] = payload.expected
    
    missing = []
    for label, count in expected.items():
        count_str = f"{count:,}" if count >= 1000 else str(count)
        pattern = rf'{label}[^0-9]*{count_str.replace(",", ",?")}' 
        if not re.search(pattern, output):
            missing.append(f"{label}:{count}")
    
    if not missing:
        return True, "All label counts found in output"
    return False, f"Missing label counts: {', '.join(missing)}"


def validate_id_pairs(output: str, payload: Any) -> tuple[bool, str]:
    """Validate ID pair extraction experiments"""
    expected_pairs = payload.expected
    found = 0
    missing = []
    for pair in expected_pairs:
        if pair[0] in output and pair[1] in output:
            found += 1
        else:
            missing.append(f"({pair[0]}, {pair[1]})")
    
    threshold = len(expected_pairs) * 0.8
    if found >= threshold:
        return True, f"Found {found}/{len(expected_pairs)} pairs (threshold: {threshold:.0f})"
    return False, f"Found only {found}/{len(expected_pairs)} pairs (threshold: {threshold:.0f}). Missing: {', '.join(missing[:3])}"


def validate_multiple_choice(output: str, payload: Any) -> tuple[bool, str]:
    """Validate multiple choice experiments"""
    if payload.expected.upper() in output.upper():
        return True, f"Found expected answer '{payload.expected}'"
    return False, f"Expected answer '{payload.expected}' not found in output"


# S-NIAH experiment configs
SNIAH_CONFIGS = {
    "s-niah-50k": {
        "total_chars": 200_000,
        "needle": "The magic number is 73628.",
        "description": "Single Needle in a 50K-token haystack",
    },
    "s-niah-200k": {
        "total_chars": 800_000,
        "needle": "The secret code is ALPHA-DELTA-GAMMA-9527.",
        "description": "Single Needle in a 200K-token haystack",
    },
    "s-niah-1m": {
        "total_chars": 4_000_000,
        "needle": "The hidden identifier is ZETA-OMEGA-42-PRIME.",
        "description": "Single Needle in a 1M-token haystack",
    },
}
