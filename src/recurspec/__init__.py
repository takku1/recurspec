"""Recurspec's evidence-gated design and evaluation tools."""

from .contract import Diagnostic, ValidationResult, validate_contract
from .evaluation import ERROR, ESCALATE, KEEP, REVERT, evaluate_change
from .inspection import check_project

__all__ = [
    "ERROR",
    "ESCALATE",
    "KEEP",
    "REVERT",
    "Diagnostic",
    "ValidationResult",
    "evaluate_change",
    "check_project",
    "validate_contract",
]
__version__ = "0.2.0"
