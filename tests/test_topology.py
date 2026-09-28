import unittest
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
from persim import bottleneck
from market_neutral.topology import (correlation_distance, persistence, summarise,
    landscape, rolling_features, fit_control_model, predict_control_model, CONTROLS)


class TopologyTests(unittest.TestCase):
    def test_square_has_one_loop_at_known_scales(self):
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        diagrams = persistence(squareform(pdist(points)))
        np.testing.assert_allclose(np.sort(diagrams["h0"][:, 1]), [1, 1, 1])
        np.testing.assert_allclose(diagrams["h1"], [[1, np.sqrt(2)]], atol=2e-7)
        self.assertEqual(diagrams["essential_h0"], 1)

    def test_triangle_fills_immediately_and_line_has_no_loop(self):
        for points in (np.array([[0, 0], [1, 0], [.5, np.sqrt(3)/2]]),
                       np.array([[0, 0], [1, 0], [3, 0], [6, 0]])):
            diagrams = persistence(squareform(pdist(points)))
            self.assertEqual(len(diagrams["h1"]), 0)
            self.assertEqual(summarise(diagrams)["h1_max"], 0)

    def test_h0_independently_matches_mst(self):
        points = np.random.default_rng(19).normal(size=(17, 4))
        distance = squareform(pdist(points))
        expected = np.sort(minimum_spanning_tree(distance).data)
        observed = np.sort(persistence(distance)["h0"][:, 1])
        np.testing.assert_allclose(observed, expected, atol=3e-7)

    def test_duplicate_points_preserve_zero_merges(self):
        diagrams = persistence(np.array([[0., 0., 1.], [0., 0., 1.], [1., 1., 0.]]))
        self.assertEqual(diagrams["zero_h0_merges"], 1)
        self.assertEqual(summarise(diagrams)["h0_mean"], .5)

    def test_correlation_distance_is_euclidean_chord_and_invariant(self):
        r = np.random.default_rng(20).normal(size=(80, 9))
        _, distance = correlation_distance(r)
        centered = r - r.mean(axis=0)
        unit = centered / np.linalg.norm(centered, axis=0)
        np.testing.assert_allclose(distance, squareform(pdist(unit.T)), atol=1e-12)
        _, rescaled = correlation_distance(r * np.arange(1, 10) + 3)
        np.testing.assert_allclose(distance, rescaled, atol=1e-12)
        order = np.arange(9)[::-1]
        permuted = persistence(distance[np.ix_(order, order)])
        for feature, value in summarise(persistence(distance)).items():
            self.assertAlmostEqual(value, summarise(permuted)[feature], places=6)

    def test_future_changes_cannot_change_past_features(self):
        rng = np.random.default_rng(21)
        dates = pd.bdate_range("2010-01-01", periods=85)
        r = pd.DataFrame(rng.normal(0, .01, (85, 7)), index=dates)
        market = pd.Series(rng.normal(0, .01, 85), index=dates)
        wanted = dates[30:55]
        before, _, _ = rolling_features(r, market, [10, 20, 30], wanted)
        changed = r.copy(); changed.iloc[55:] = rng.normal(4, 10, (30, 7))
        changed_m = market.copy(); changed_m.iloc[55:] = 9
        after, _, _ = rolling_features(changed, changed_m, [10, 20, 30], wanted)
        pd.testing.assert_frame_equal(before, after)
        with self.assertRaises(ValueError):
            rolling_features(r, market, [30], dates[28:30])

    def test_landscape_matches_analytic_tents(self):
        x = np.array([0., 1., 2., 3., 4.])
        expected = np.array([[0, 1, 2, 1, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]])
        np.testing.assert_array_equal(landscape([[0, 4], [1, 3]], x, 3), expected)
        np.testing.assert_array_equal(landscape([], x, 2), np.zeros((2, 5)))

    def test_small_metric_perturbation_respects_bottleneck_bound(self):
        a = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        b = a.copy(); b[0] += [.03, -.02]
        da, db = squareform(pdist(a)), squareform(pdist(b))
        pa, pb = persistence(da), persistence(db)
        for dim in ("h0", "h1"):
            self.assertLessEqual(bottleneck(pa[dim], pb[dim]), np.abs(da-db).max()+2e-6)

    def test_development_model_reconstructs_known_relationship(self):
        rng = np.random.default_rng(22)
        data = pd.DataFrame(rng.normal(size=(60, 3)), columns=CONTROLS,
                            index=pd.bdate_range("2010-01-01", periods=60))
        data["target"] = 2 + data[CONTROLS[0]] - 3 * data[CONTROLS[1]] + .5 * data[CONTROLS[2]]
        train, later = data.iloc[:40], data.iloc[40:]
        model = fit_control_model(train, "target")
        np.testing.assert_allclose(predict_control_model(later, model), later.target, atol=1e-12)
        np.testing.assert_allclose(model["center"], train[list(CONTROLS)].mean())
        self.assertEqual(model["fitted_rows"], 40)

    def test_invalid_geometry_is_rejected(self):
        with self.assertRaises(ValueError):
            correlation_distance(np.ones((50, 4)))
        for distance in ([[0, 1], [2, 0]], [[0, -1], [-1, 0]], [[1, 2], [2, 0]]):
            with self.assertRaises(ValueError):
                persistence(distance)


if __name__ == "__main__":
    unittest.main()
