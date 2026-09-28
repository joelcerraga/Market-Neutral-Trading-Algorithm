"""Independent numerical checks for dependent-return inference and controls."""
from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
import pandas as pd
from market_neutral.inference import stationary_indices, stationary_mean_interval, hac_mean_interval
from market_neutral.comparison import match_gross_exposure, load_comparison_protocol
from market_neutral.portfolio import neutral_weights


class ComparisonChecks(unittest.TestCase):
    def test_stationary_bootstrap_matches_exact_mean_variance(self):
        # Finite-sample formula in Nordman (2009), Equation 3.
        x = np.sin(np.arange(45) / 4) + np.arange(45) / 70
        n, length = len(x), 7
        centered, q = x - x.mean(), 1 - 1 / length
        long_run = centered @ centered / n
        for lag in range(1, n):
            weight = (1 - lag / n) * q ** lag + (lag / n) * q ** (n - lag)
            long_run += 2 * weight * (centered[lag:] @ centered[:-lag] / n)
        measured = stationary_mean_interval(x, length, 12000, 17)["bootstrap_standard_error"] ** 2
        self.assertAlmostEqual(measured, long_run / n, delta=.06 * long_run / n)

    def test_circular_continuation_and_constant_series(self):
        indices = stationary_indices(9, 50, 1e30, 23)
        np.testing.assert_array_equal(indices[:, 1:], (indices[:, :-1] + 1) % 9)
        result = stationary_mean_interval(np.full(30, .002), 5, 300, 19)
        self.assertAlmostEqual(result["daily_lower"], .002)
        self.assertAlmostEqual(result["daily_upper"], .002)

    def test_paired_mean_interval_is_translation_equivariant(self):
        x = np.sin(np.arange(80) / 5) / 100
        a = stationary_mean_interval(x, 10, 500, 42)
        b = stationary_mean_interval(x + .003, 10, 500, 42)
        for field in ["daily_mean", "daily_lower", "daily_upper"]:
            self.assertAlmostEqual(b[field] - a[field], .003, places=12)

    def test_hac_matches_bartlett_quadratic_form(self):
        x = np.array([.1, .3, -.2, .05, -.1, .2, .07, .03])
        lags, n = 3, len(x)
        distances = np.abs(np.arange(n)[:, None] - np.arange(n)[None, :])
        kernel = np.maximum(1 - distances / (lags + 1), 0)
        centered = x - x.mean()
        variance_of_mean = centered @ kernel @ centered / n ** 2
        self.assertAlmostEqual(hac_mean_interval(x, lags)["hac_standard_error"] ** 2, variance_of_mean, places=14)

    def test_matching_gross_preserves_neutrality_and_never_levers_up(self):
        beta = np.linspace(.5, 1.8, 8)
        a = neutral_weights(np.array([9., -2, 1, 2, -1, 4, -3, .5]), beta, 1, .08)
        b = neutral_weights(np.arange(8.) ** 2, beta, 1, .08)
        base = pd.DataFrame([a, a])
        graph = pd.DataFrame([b, np.zeros(8)])
        mb, mg = match_gross_exposure(base, graph)
        np.testing.assert_allclose(mb.abs().sum(axis=1), mg.abs().sum(axis=1), atol=1e-12)
        for original, matched in [(base, mb), (graph, mg)]:
            self.assertTrue((matched.abs() <= original.abs() + 1e-12).all().all())
            np.testing.assert_allclose(matched.sum(axis=1), 0, atol=1e-12)
            np.testing.assert_allclose(matched.to_numpy() @ beta, 0, atol=1e-12)
            np.testing.assert_allclose(matched.iloc[1], 0, atol=1e-12)

    def test_frozen_comparison_protocol_rejects_edits(self):
        source = Path(__file__).resolve().parents[1] / "protocol"
        with tempfile.TemporaryDirectory() as folder:
            shutil.copytree(source, Path(folder) / "protocol")
            load_comparison_protocol(folder)
            path = Path(folder) / "protocol/graph-comparison-v1.json"
            path.write_text(path.read_text() + " ")
            with self.assertRaisesRegex(ValueError, "frozen hash"):
                load_comparison_protocol(folder)


if __name__ == "__main__":
    unittest.main()
