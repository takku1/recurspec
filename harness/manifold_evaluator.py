#!/usr/bin/env python3
"""
manifold_evaluator.py — Cumulative System Quality Q(S) Manifold Calculator.
Computes the weighted geometric mean over 7 quality dimensions:
q_arch, q_impl, q_epistemic, q_perf, q_complex, q_doc, q_ratchet.
"""

import math
from typing import Dict

DEFAULT_WEIGHTS = {
    "q_arch": 0.20,
    "q_impl": 0.20,
    "q_epistemic": 0.15,
    "q_perf": 0.15,
    "q_complex": 0.10,
    "q_doc": 0.10,
    "q_ratchet": 0.10,
}

def compute_cumulative_quality(scores: Dict[str, float], weights: Dict[str, float] = DEFAULT_WEIGHTS) -> float:
    """
    Computes Q(S) = exp( sum( w_i * ln(q_i) ) / sum(w_i) )
    Clamps q_i to [0.001, 1.0] to prevent ln(0) collapse.
    """
    log_sum = 0.0
    weight_sum = 0.0

    for dim, w in weights.items():
        val = scores.get(dim, 0.5)
        clamped_val = max(0.001, min(1.0, val))
        log_sum += w * math.log(clamped_val)
        weight_sum += w

    if weight_sum <= 0:
        return 0.0

    return math.exp(log_sum / weight_sum)

if __name__ == "__main__":
    # Test example: Balanced high quality
    sample_scores_good = {
        "q_arch": 0.90,
        "q_impl": 0.98,
        "q_epistemic": 0.85,
        "q_perf": 0.88,
        "q_complex": 0.82,
        "q_doc": 0.90,
        "q_ratchet": 0.80,
    }
    q_good = compute_cumulative_quality(sample_scores_good)
    print(f"Sample Good Q(S): {q_good:.4f}")

    # Test example: One metric collapsed (e.g. docs desynced to 0.05)
    sample_scores_collapsed = sample_scores_good.copy()
    sample_scores_collapsed["q_doc"] = 0.05
    q_bad = compute_cumulative_quality(sample_scores_collapsed)
    print(f"Sample Collapsed Q(S): {q_bad:.4f} (Notice how geometric mean collapses!)")
