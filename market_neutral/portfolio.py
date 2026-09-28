"""Dollar and estimated-beta neutrality with limits preserved by uniform scaling."""
import numpy as np


def neutral_weights(score, beta, gross_limit=1.0, position_limit=0.08):
    score, beta = np.asarray(score, dtype=float), np.asarray(beta, dtype=float)
    if score.ndim != 1 or score.shape != beta.shape or not np.isfinite(score).all() or not np.isfinite(beta).all():
        raise ValueError("Score and beta must be aligned, finite vectors")
    if len(score) < 3 or not 0 < gross_limit <= 2 or not 0 < position_limit <= 1:
        raise ValueError("Invalid portfolio dimensions or limits")
    exposures = np.column_stack([np.ones(len(score)), beta])
    neutral = score - exposures @ np.linalg.lstsq(exposures, score, rcond=None)[0]
    gross = np.abs(neutral).sum()
    if gross <= 1e-10 * max(1.0, np.linalg.norm(score)):
        return np.zeros_like(score)
    weights = neutral * (gross_limit / gross)
    weights *= min(1.0, position_limit / np.abs(weights).max())
    return weights
