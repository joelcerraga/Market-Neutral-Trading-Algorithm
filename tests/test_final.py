import unittest
import numpy as np
import pandas as pd
from market_neutral.final_data import overlap_audit
from market_neutral.final_inference import confidence_levels, fixed_family_intervals, evidence_gate, CONTRASTS
from market_neutral.historical import phase_inputs


class FinalEvaluationTests(unittest.TestCase):
    def test_overlap_ignores_constant_price_rescaling(self):
        dates = pd.bdate_range("2019-01-01",periods=5)
        original = pd.Series([10.,11.,10.5,12.,11.],index=dates)
        result = overlap_audit(original,original*7.3,1e-5)
        self.assertLess(result["max_abs_overlap_return_change"],1e-14)
        self.assertAlmostEqual(result["median_adjusted_price_ratio"],7.3)

    def test_overlap_rejects_return_revision_and_calendar_deletion(self):
        dates = pd.bdate_range("2019-01-01",periods=5)
        original = pd.Series([10.,11.,10.5,12.,11.],index=dates)
        revised = original.copy();revised.iloc[2] *= 1.001
        with self.assertRaises(ValueError): overlap_audit(original,revised,1e-5)
        with self.assertRaises(ValueError): overlap_audit(original,original.iloc[1:],1e-5)

    def test_bonferroni_tail_budget_is_the_declared_family_alpha(self):
        levels = confidence_levels(.05,3)
        self.assertAlmostEqual(levels["pointwise"],.95)
        self.assertAlmostEqual(3*(1-levels["bonferroni"]),.05)
        with self.assertRaises(ValueError):confidence_levels(.05,0)

    def test_joint_resampling_preserves_constant_paired_difference(self):
        dates = pd.bdate_range("2020-01-01",periods=40)
        base = np.linspace(-.01,.01,40)
        paired = pd.DataFrame({"baseline":base,"graph":base+.001},index=dates)
        settings={"family_alpha":.05,"block_lengths":[5],"stationary_bootstrap_replicates":300,
                  "seed":7,"primary_block_length":5,"hac_lags":3}
        intervals,samples = fixed_family_intervals(paired,settings)
        np.testing.assert_allclose(samples.graph_minus_baseline_mean,.001,atol=1e-15)
        np.testing.assert_allclose(samples.graph_net_mean-samples.baseline_net_mean,.001,atol=1e-15)
        selected=intervals.loc[intervals.contrast=="graph_minus_baseline_mean"]
        np.testing.assert_allclose(selected.annualised_lower,.252,atol=1e-12)
        np.testing.assert_allclose(selected.annualised_upper,.252,atol=1e-12)
        for (contrast,method),frame in intervals.groupby(["contrast","method"]):
            by=frame.set_index("interval_type")
            self.assertLessEqual(by.loc["bonferroni","annualised_lower"],by.loc["pointwise","annualised_lower"]+1e-14)
            self.assertGreaterEqual(by.loc["bonferroni","annualised_upper"],by.loc["pointwise","annualised_upper"]-1e-14)

    def test_gate_cannot_pass_on_a_relative_improvement_alone(self):
        intervals=pd.DataFrame({"contrast":CONTRASTS,"method":"stationary bootstrap","block_or_lags":10,
                                "interval_type":"bonferroni","annualised_lower":[-.05,-.02,.01]})
        matched=pd.DataFrame({"method":["stationary bootstrap"],"block_or_lags":[10],"annualised_lower":[.005]})
        gate=evidence_gate(-.01,intervals,matched)
        self.assertFalse(gate["all_conditions_met"])
        self.assertTrue(gate["conditions"]["positive_incremental_mean"])
        self.assertFalse(gate["conditions"]["positive_absolute_mean"])

    def test_final_phase_uses_prior_close_decision_without_resetting_history(self):
        dates=pd.to_datetime(["2019-12-30","2019-12-31","2020-01-02","2020-01-03"])
        r=pd.DataFrame({"A":[.01,.02,.03,.04],"B":[-.01,-.02,-.03,-.04]},index=dates)
        w=pd.DataFrame({"A":[.1,.2,.3,.4],"B":[-.1,-.2,-.3,-.4]},index=dates)
        beta=pd.DataFrame(1.,index=dates,columns=r.columns)
        protocol={"allowed_phases":["final_test"],"phases":{"final_test":["2020-01-01","2025-12-31"]}}
        selected,execution,exposures=phase_inputs(r,w,beta,protocol,"final_test")
        np.testing.assert_array_equal(execution.iloc[0],[.2,-.2])
        self.assertEqual(str(selected.index[0].date()),"2020-01-02")
        with self.assertRaises(ValueError):phase_inputs(r,w,beta,protocol,"unreleased")


if __name__=="__main__":unittest.main()
