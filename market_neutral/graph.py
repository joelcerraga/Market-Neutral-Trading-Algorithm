"""Positive-correlation graph and constant-preserving heat diffusion."""
import numpy as np
from scipy.linalg import eigh


def correlation_graph(history, neighbours=5, minimum_correlation=0.20):
    values = np.asarray(history, dtype=float)
    if values.ndim != 2 or values.shape[0] < 3 or not np.isfinite(values).all():
        raise ValueError("Graph history must be a finite time-by-asset matrix")
    if (values.std(axis=0, ddof=1) < 1e-12).any():
        raise ValueError("A constant series has undefined correlation")
    n = values.shape[1]
    if not 1 <= neighbours < n or not 0 <= minimum_correlation < 1:
        raise ValueError("Invalid graph parameters")
    correlation = np.clip(np.corrcoef(values, rowvar=False), -1, 1)
    candidate = np.where(correlation > minimum_correlation, correlation, 0.0)
    np.fill_diagonal(candidate, 0.0)
    directed = np.zeros_like(candidate)
    for i in range(n):
        nearest = np.argsort(-candidate[i], kind="stable")[:neighbours]
        directed[i, nearest] = candidate[i, nearest]
    # Union k-nearest-neighbour graph: degree can exceed k after symmetrising.
    adjacency = np.maximum(directed, directed.T)
    degree = adjacency.sum(axis=1)
    scale = degree.mean() if degree.mean() > 1e-12 else 1.0
    laplacian = (np.diag(degree) - adjacency) / scale
    return correlation, adjacency, laplacian


def heat_diffusion(signal, laplacian, diffusion_time=1.0):
    signal = np.asarray(signal, dtype=float)
    laplacian = np.asarray(laplacian, dtype=float)
    if laplacian.shape != (len(signal), len(signal)) or not np.isfinite(laplacian).all():
        raise ValueError("Laplacian dimensions must match a finite signal")
    if not np.isfinite(signal).all() or not np.isfinite(diffusion_time) or diffusion_time < 0:
        raise ValueError("Invalid signal or diffusion time")
    if not np.allclose(laplacian, laplacian.T, atol=1e-10):
        raise ValueError("Laplacian must be symmetric")
    eigenvalues, eigenvectors = eigh(laplacian)
    if eigenvalues.min() < -1e-9:
        raise ValueError("Laplacian must be positive semidefinite")
    return eigenvectors @ (np.exp(-diffusion_time * np.maximum(eigenvalues, 0))
                           * (eigenvectors.T @ signal))
