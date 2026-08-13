"""Recurspec's evidence-gated design and evaluation tools."""

from .evaluation import ERROR, ESCALATE, KEEP, REVERT, evaluate_change

__all__ = ["ERROR", "ESCALATE", "KEEP", "REVERT", "evaluate_change"]
__version__ = "0.1.0"
