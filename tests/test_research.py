"""Independent mathematical, timing and ledger checks, using the standard library."""
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import expm
from market_neutral.config import ResearchConfig
from market_neutral.data import generate_synthetic, simple_returns, load_prices_csv
from market_neutral.graph import correlation_graph, heat_diffusion
from market_neutral.portfolio import neutral_weights
from market_neutral.strategy import build_decisions
from market_neutral.backtest import execute_targets, run_backtest


class ResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = ResearchConfig(observations=90, assets=8, sectors=2,
                                    correlation_window=20, beta_window=20,
                                    volatility_window=15, signal_window=3, neighbours=2,
                                    position_limit=.3)
        cls.data = generate_synthetic(cls.config)
        cls.returns, cls.market = simple_returns(cls.data)

    def test_synthetic_reproducible(self):
        pd.testing.assert_frame_equal(self.data.prices, generate_synthetic(self.config).prices)

    def test_constant_signal_is_preserved_and_heat_matches_expm(self):
        _, _, lap = correlation_graph(self.returns.iloc[:30], neighbours=2)
        np.testing.assert_allclose(heat_diffusion(np.ones(8), lap), np.ones(8), atol=1e-12)
        x = np.arange(8, dtype=float)
        np.testing.assert_allclose(heat_diffusion(x, lap, .7), expm(-.7 * lap) @ x, atol=1e-12)

    def test_graph_energy_cannot_increase_under_diffusion(self):
        _, w, lap = correlation_graph(self.returns.iloc[:30], neighbours=2)
        np.testing.assert_allclose(w, w.T)
        self.assertTrue(np.all(np.diag(w) == 0))
        x = np.array([2., -1, .4, .3, -.3, 1, 2, -2])
        smooth = heat_diffusion(x, lap)
        self.assertLessEqual(smooth @ lap @ smooth, x @ lap @ x + 1e-12)

    def test_disconnected_graph_produces_no_diffusion_residual(self):
        x = np.arange(5, dtype=float)
        np.testing.assert_allclose(heat_diffusion(x, np.zeros((5, 5))), x)

    def test_neutrality_and_caps_survive_concentrated_score(self):
        score = np.array([100., -1, 2, 3, -.2, 7, -5, 1])
        beta = np.linspace(.6, 1.5, 8)
        w = neutral_weights(score, beta, 1.0, .08)
        self.assertAlmostEqual(w.sum(), 0, places=12)
        self.assertAlmostEqual(w @ beta, 0, places=12)
        self.assertLessEqual(np.abs(w).sum(), 1 + 1e-12)
        self.assertLessEqual(np.abs(w).max(), .08 + 1e-12)

    def test_identical_betas_and_zero_scores_are_well_defined(self):
        w = neutral_weights(np.arange(8.), np.ones(8), 1, .2)
        self.assertAlmostEqual(w.sum(), 0, places=12)
        np.testing.assert_array_equal(neutral_weights(np.zeros(8), np.ones(8)), np.zeros(8))

    def test_future_prices_cannot_change_past_decisions(self):
        before = build_decisions(self.returns, self.market, self.config)
        modified, market = self.returns.copy(), self.market.copy()
        modified.iloc[60:] = modified.iloc[60:] * -1.7 + .01
        market.iloc[60:] = market.iloc[60:] * 2 - .01
        after = build_decisions(modified, market, self.config)
        for name in before.targets:
            pd.testing.assert_frame_equal(before.targets[name].iloc[:60], after.targets[name].iloc[:60])
        pd.testing.assert_frame_equal(before.betas.iloc[:60], after.betas.iloc[:60])

    def test_decision_cannot_earn_same_or_next_close_return(self):
        dates = pd.date_range("2024-01-01", periods=4)
        r = pd.DataFrame({"A": [0, .5, .2, 0]}, index=dates)
        decision = pd.DataFrame({"A": [.5, .5, .5, .5]}, index=dates)
        beta = pd.DataFrame({"A": [1., 1, 1, 1]}, index=dates)
        cfg = replace(self.config, position_limit=1, trading_cost_bps=0, annual_borrow_rate=0)
        result = run_backtest(r, decision, beta, cfg)
        self.assertAlmostEqual(result.ledger.net_return.iloc[0], 0)
        self.assertAlmostEqual(result.ledger.net_return.iloc[1], 0)
        self.assertAlmostEqual(result.ledger.net_return.iloc[2], .1)
        self.assertEqual(result.execution_weights.iloc[-1, 0], 0)

    def test_entry_and_liquidation_fee_match_closed_form(self):
        dates = pd.date_range("2024-01-01", periods=2)
        r = pd.DataFrame({"A": [0., 0.]}, index=dates)
        w = pd.DataFrame({"A": [.5, .5]}, index=dates)
        cfg = replace(self.config, position_limit=1, trading_cost_bps=10, annual_borrow_rate=0)
        result = execute_targets(r, w, cfg)
        expected = cfg.initial_capital / (1 + .001 * .5) * (1 - .001 * .5)
        self.assertAlmostEqual(result.ledger.nav.iloc[-1], expected, places=7)

    def test_price_drift_creates_turnover_even_when_target_unchanged(self):
        dates = pd.date_range("2024-01-01", periods=2)
        r = pd.DataFrame({"A": [0., .1]}, index=dates)
        w = pd.DataFrame({"A": [.5, .5]}, index=dates)
        cfg = replace(self.config, position_limit=1, trading_cost_bps=0, annual_borrow_rate=0)
        result = execute_targets(r, w, cfg, liquidate_at_end=False)
        # 50,000 becomes 55,000; target is half of 105,000 => sell 2,500.
        self.assertAlmostEqual(result.traded_notionals.iloc[1, 0], -2500, places=8)

    def test_borrow_accrues_over_calendar_weekend(self):
        dates = pd.to_datetime(["2024-01-05", "2024-01-08"])
        r = pd.DataFrame({"A": [0., 0.], "B": [0., 0.]}, index=dates)
        w = pd.DataFrame({"A": [.5, .5], "B": [-.5, -.5]}, index=dates)
        cfg = replace(self.config, position_limit=1, trading_cost_bps=0, annual_borrow_rate=.0365)
        result = execute_targets(r, w, cfg)
        self.assertAlmostEqual(result.ledger.borrow_cost.iloc[1], 15, places=8)

    def test_full_run_accounting_and_neutrality(self):
        decisions = build_decisions(self.returns, self.market, self.config)
        for target in decisions.targets.values():
            result = run_backtest(self.returns, target, decisions.betas, self.config)
            ledger = result.ledger
            np.testing.assert_allclose(ledger.net_return,
                ledger.gross_return - ledger.trading_cost_return - ledger.borrow_cost_return, atol=1e-12)
            self.assertLess(ledger.net_exposure.abs().max(), 1e-10)
            self.assertLess(ledger.estimated_beta_exposure.abs().max(), 1e-10)
            self.assertLessEqual(ledger.max_position.max(), self.config.position_limit + 1e-12)
            self.assertEqual(ledger.gross_exposure.iloc[-1], 0.)

    def test_price_loader_rejects_missing_and_unsorted_data(self):
        frame = self.data.prices.join(self.data.market)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            frame.iloc[::-1].to_csv(path)
            with self.assertRaises(ValueError):
                load_prices_csv(path, "SYN_MARKET")
            frame.iloc[10, 0] = np.nan
            frame.to_csv(path)
            with self.assertRaises(ValueError):
                load_prices_csv(path, "SYN_MARKET")

    def test_loader_preserves_labels_and_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            self.data.prices.join(self.data.market).to_csv(path)
            loaded = load_prices_csv(path, "SYN_MARKET")
            np.testing.assert_allclose(loaded.prices, self.data.prices)
            self.assertEqual(list(loaded.prices.columns), list(self.data.prices.columns))


if __name__ == "__main__":
    unittest.main()
