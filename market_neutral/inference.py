"""Paired-return uncertainty, conditional on the observed backtest policies."""
import numpy as np
from scipy.stats import norm


def stationary_indices(observations, replicates, mean_block_length, seed):
    """Circular stationary bootstrap: restart probability 1 / mean length."""
    if observations < 2 or replicates < 2 or mean_block_length < 1:
        raise ValueError("Need at least two observations/replicates and mean length >= 1")
    rng = np.random.default_rng(seed)
    indices = np.empty((replicates, observations), dtype=np.int32)
    indices[:, 0] = rng.integers(0, observations, size=replicates)
    for t in range(1, observations):
        restart = rng.random(replicates) < 1.0 / mean_block_length
        new_start = rng.integers(0, observations, size=replicates)
        indices[:, t] = np.where(restart, new_start, (indices[:, t - 1] + 1) % observations)
    return indices


def stationary_mean_interval(values, mean_block_length=10, replicates=5000,
                             seed=20260921, confidence_level=.95):
    """Percentile interval for the daily mean; input is the paired difference."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Need a finite one-dimensional return-difference series")
    if not 0 < confidence_level < 1:
        raise ValueError("Invalid confidence level")
    indices = stationary_indices(len(x), replicates, mean_block_length, seed)
    means = x[indices].mean(axis=1)
    alpha = (1 - confidence_level) / 2
    lower, upper = np.quantile(means, [alpha, 1 - alpha])
    return {"daily_mean": float(x.mean()), "daily_lower": float(lower),
            "daily_upper": float(upper), "bootstrap_standard_error": float(means.std(ddof=1))}


def hac_mean_interval(values, lags=10, confidence_level=.95):
    """Newey-West/Bartlett long-run variance for an intercept-only mean."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Need a finite one-dimensional return-difference series")
    if not isinstance(lags, int) or not 0 <= lags < len(x):
        raise ValueError("HAC lag count must be an integer below sample length")
    if not 0 < confidence_level < 1:
        raise ValueError("Invalid confidence level")
    centered = x - x.mean()
    n = len(x)
    long_run_variance = float(centered @ centered / n)
    for lag in range(1, lags + 1):
        covariance = float(centered[lag:] @ centered[:-lag] / n)
        long_run_variance += 2 * (1 - lag / (lags + 1)) * covariance
    if long_run_variance < -1e-12:
        raise ArithmeticError("Unexpected negative Bartlett long-run variance")
    standard_error = np.sqrt(max(long_run_variance, 0) / n)
    critical = norm.ppf((1 + confidence_level) / 2)
    return {"daily_mean": float(x.mean()), "daily_lower": float(x.mean() - critical * standard_error),
            "daily_upper": float(x.mean() + critical * standard_error),
            "hac_standard_error": float(standard_error), "long_run_variance": float(max(long_run_variance, 0))}
