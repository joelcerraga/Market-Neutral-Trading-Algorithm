"""Build the fifth explanatory notebook; execute separately to retain outputs."""
from pathlib import Path
import json
import sys
import textwrap
import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'paper'))
from update_manuscript import harvard_reference


def main():
    cells=[]
    def md(s):cells.append(nbformat.v4.new_markdown_cell(textwrap.dedent(s).strip()))
    def code(s):cells.append(nbformat.v4.new_code_cell(textwrap.dedent(s).strip()))
    md('''
    # Milestone 5 — Final evaluation on the reserved historical period
    **Joel Cerraga · Market-Neutral Trading Algorithm**

    The frozen design compares the existing primary graph strategy with the baseline on 2020–2025. It keeps all 22 declared cases and transfers the topology controls without refitting. No topology trading overlay is introduced. The test is now observed; future rule changes need new evidence.

    As White (2000) explains in *A Reality Check for Data Snooping*, searching over alternatives changes the meaning of apparent success. Bailey et al. (2017), in *The probability of backtest overfitting*, also discuss repeated selection. This project therefore records the finite comparison and necessary evidence conditions before acquisition. It does not claim to implement either paper's complete correction.

    “Reserved” describes this project's chronology. The years are public history and the basket contains retrospectively selected survivors. As Shumway (1997) explains in *The Delisting Bias in CRSP Data*, missing adverse outcomes matter for historical inference. That limitation is not removed by a protocol hash. Final PDF compilation remains deferred.
    ''')
    code('''
    from pathlib import Path
    import json, sys, inspect
    import numpy as np
    import pandas as pd
    from IPython.display import display, Markdown, Image
    ROOT = Path.cwd()
    if not (ROOT / "market_neutral").exists():
        ROOT = ROOT.parent
    sys.path.insert(0, str(ROOT))
    from market_neutral.historical import sha256
    from market_neutral.final_data import load_final_protocol, assemble_final_dataset, overlap_audit
    from market_neutral.final_evaluation import evaluate_final, final_topology
    from market_neutral.final_inference import fixed_family_intervals
    from market_neutral.final_plots import create_final_figures
    output = ROOT / "outputs/final"
    print("Working folder:", ROOT.name)
    ''')
    md(r'''
    ## 1. Verify the protocol and separate observation vintage

    Yahoo Finance (2026b) supplies the requested final vintage. The old cache remains unchanged. Each series must have the exact SPY calendar, positive complete observations and no return above the predeclared review threshold. The new warm-up is not spliced into the old adjusted-price series.

    Equation 28 compares overlapping **returns**, permitting a constant adjustment factor while rejecting material revisions:

    $$\max_{t\in\mathcal O}|r_t^{\mathrm{new}}-r_t^{\mathrm{old}}|\leq 10^{-5}.\tag{28}$$

    The tolerance is 0.1 basis points, fixed before acquisition. The retained snapshot guard fixes the audited vintage for subsequent replay; its recording time is separate from the earlier design lock.
    ''')
    code('''
    protocol = load_final_protocol(ROOT)
    dataset, audit = assemble_final_dataset(ROOT)
    lock = json.loads((ROOT / "protocol/final-evaluation-v1.lock.json").read_text())
    release = json.loads((output / "holdout-release.json").read_text())
    assert pd.Timestamp(lock["locked_utc"]) < pd.Timestamp(release["release_started_utc"])
    assert audit.rows.eq(1761).all() and audit.overlap_returns.eq(252).all()
    assert audit.max_abs_overlap_return_change.max() <= 1e-5
    print("Final design hash:", dataset.metadata["protocol_sha256"])
    print("Audited input hash:", dataset.metadata["input_sha256"])
    print("Largest overlapping return change, basis points:", 10000*audit.max_abs_overlap_return_change.max())
    display(audit[["rows", "first_date", "last_date", "missing", "max_abs_overlap_return_change"]])
    print(inspect.getsource(overlap_audit))
    ''')
    md('''
    ## 2. Replay every scenario and verify the artifact repair

    The decision at close t executes at close t+1. A flat USD 100,000 book starts the final phase; entry, drift trades, calendar-day borrow and terminal liquidation are included. Calendar years do not reset positions. The finite set contains 16 model/fee cases, four extra borrow cases and two matched-gross cases.

    The first run exposed a genuine artifact failure: one 10 bps graph ledger was empty. Its in-memory summary was present. The original manifest is preserved, and verified atomic writes now check the saved bytes. Every unaffected numerical output must reproduce its original hash; the repaired ledger must reconcile with the unchanged summary. Later executions require every current numeric output to reproduce too.
    ''')
    code('''
    initial = json.loads((ROOT / "validation/final-initial-run-manifest.json").read_text())
    repair_path = ROOT / "validation/final-artifact-repair.json"
    repair = json.loads(repair_path.read_text())
    previous = json.loads((output / "run-manifest.json").read_text())
    was_repaired = repair["status"] == "verified"
    results, summary, intervals, manifest = evaluate_final(ROOT, dataset)
    affected = repair["affected_output"]
    assert set(initial["files"]) == set(manifest["files"])
    for name, expected in initial["files"].items():
        if name != affected:
            assert manifest["files"][name] == expected, name
    if was_repaired:
        assert manifest["files"] == previous["files"]
    repaired_ledger = pd.read_csv(output / affected, index_col=0, parse_dates=True)
    recorded = summary.loc[(summary.model == "graph_tau_1") &
                           (summary.trading_cost_bps == 10) & (summary.annual_borrow_rate == .02)].iloc[0]
    assert len(repaired_ledger) == 1508
    np.testing.assert_allclose((1+repaired_ledger.net_return).prod()-1, recorded.total_return, atol=1e-11)
    repair.update(status="verified", unaffected_hashes_reproduced=len(initial["files"])-1,
                  repaired_rows=len(repaired_ledger), repaired_sha256=sha256(output / affected),
                  summary_sha256_unchanged=manifest["files"]["final-summary.csv"],
                  final_protocol_sha256=manifest["protocol_sha256"])
    repair_path.write_text(json.dumps(repair, indent=2)+"\\n")
    create_final_figures(ROOT)
    assert len(summary) == 22 and manifest["test_sessions"] == 1508
    print("All 22 cases completed; initial unaffected hashes reproduced:", len(initial["files"])-1)
    print("Repaired ledger:", len(repaired_ledger), "sessions; original summary unchanged")
    ''')
    md('''
    ## 3. Inspect absolute performance before relative improvement

    Both primary strategies lose money at default costs. The graph loses less, but its negative CAGR does not meet the predeclared profitability condition. The flat line is a no-trade **zero-cash-rate** comparator consistent with the ledger, not a historical risk-free return series.

    Estimated dollar/beta neutrality is a portfolio constraint. The realised rolling beta below is an empirical diagnostic and need not equal zero.
    ''')
    code('''
    primary = summary.loc[summary.purpose == "primary"].set_index("model")
    display(primary[["annualised_return", "total_return", "annualised_volatility",
                     "maximum_drawdown", "realized_market_beta", "mean_gross_exposure"]])
    display(Image(filename=str(output / "13-final-performance.png")))
    display(Markdown((output / "milestone-5-results.md").read_text()))
    ''')
    md(r'''
    ## 4. Examine the fixed three-mean family

    Politis and Romano (1994), in *The Stationary Bootstrap*, provide the dependence-preserving construction. Nordman (2009), in *A note on the stationary bootstrap's variance*, gives the finite-variance relationship used in the numerical checks. The same sampled date blocks are applied to baseline, graph and their paired difference. Newey and West (1987) provide the HAC cross-check.

    $$\xi_t=(R_t^{B,\mathrm{net}},R_t^{G,\mathrm{net}},R_t^{G,\mathrm{net}}-R_t^{B,\mathrm{net}})^\top,\qquad\widehat\mu_j=252\bar\xi_j.\tag{29}$$

    As Lehmann and Romano (2005) explain in *Testing Statistical Hypotheses*, individual and family-wise error are different quantities. The fixed family has three means, so each two-sided adjusted interval has nominal coverage 1−0.05/3, approximately 98.33%:

    $$\Pr\!\left(\bigcup_{j=1}^{3}\{\mu_j\notin I_j\}\right)\leq\sum_{j=1}^{3}\Pr(\mu_j\notin I_j)\leq0.05.\tag{30}$$

    This is an approximate joint-coverage design because the marginal intervals are approximate. It does not correct survivor selection, structural change or unlimited earlier searches. The estimand is an annualised **arithmetic mean**, not CAGR. All block lengths and both reporting levels remain in the CSV.
    ''')
    code('''
    display(intervals.loc[(intervals.method == "stationary bootstrap") &
                          (intervals.block_or_lags == 10)])
    samples = pd.read_csv(output / "primary-bootstrap-means.csv")
    np.testing.assert_allclose(samples.graph_minus_baseline_mean,
                               samples.graph_net_mean-samples.baseline_net_mean, atol=2e-14)
    print(inspect.getsource(fixed_family_intervals))
    display(Image(filename=str(output / "14-final-inference.png")))
    print(json.dumps(manifest["evidence_gate"], indent=2))
    ''')
    md('''
    ## 5. Keep the exposure, cost and annual controls

    Matched gross reduces both decision portfolios to the smaller original gross before the execution delay. It does not equalise all risks. Its paired interval still includes zero. The fee and borrow cases are sensitivities, not candidates to promote after the result.

    The arithmetic gross contribution minus trading and borrow drag reconciles with the arithmetic net mean. It is not a decomposition of CAGR. Annual returns compound within one continuous ledger, without resets or excluded years.
    ''')
    code('''
    display(summary.loc[summary.purpose == "matched gross control",
                        ["model", "annualised_return", "mean_gross_exposure", "mean_turnover"]])
    display(pd.read_csv(output / "matched-uncertainty.csv"))
    display(summary.loc[summary.annual_borrow_rate == .02].pivot(
        index="model", columns="trading_cost_bps", values="annualised_return"))
    annual = pd.read_csv(output / "calendar-year-results.csv")
    display(annual.pivot(index="year", columns="model", values="net_return"))
    for model in ["baseline", "graph_tau_1"]:
        np.testing.assert_allclose((1+annual.loc[annual.model == model, "net_return"]).prod()-1,
                                   primary.loc[model, "total_return"], atol=1e-11)
    display(Image(filename=str(output / "15-final-costs.png")))
    ''')
    md('''
    ## 6. Transfer topology controls without refitting

    All four descriptors are extracted at 63, 126 and 252 sessions. The saved development-only means, scales and coefficients are reused unchanged. Negative final R² indicates that this fixed approximation transfers poorly relative to the phase-mean benchmark; it does not prove profitable information in the residuals.

    As Chazal et al. (2014) explain in *Persistence stability for geometric complexes*, metric perturbations control diagram changes. Passing that bound is distinct from stable cross-window rankings or a transferable statistical relationship.
    ''')
    code('''
    assert sha256(ROOT / "outputs/topology/control-models.json") == protocol["topology_control_models_sha256"]
    assert manifest["topology"]["control_models_refitted"] is False
    features = pd.read_csv(output / "topology/features.csv", index_col="date", parse_dates=True)
    scores = pd.read_csv(output / "topology/control-model-scores.csv")
    checks = pd.read_csv(output / "topology/diagram-stability.csv")
    assert len(features) == 4524 and len(checks) == 288
    assert (checks.bottleneck_distance <= checks.max_distance_change + 2e-6).all()
    display(scores.pivot(index="feature", columns="window", values="r2"))
    print(inspect.getsource(final_topology))
    display(Image(filename=str(output / "16-final-topology-transfer.png")))
    ''')
    md('''
    ## 7. Explore the 72 monthly landscapes

    As Bubenik (2015) explains in *Statistical topological data analysis using persistence landscapes*, interval lifetimes can be represented by ordered tent functions. The HTML companion pairs five landscape layers with the actual birth/death diagram at each monthly close. All finite intervals enter the descriptor calculation even when more than five overlap.

    Open the file in a browser to rotate, hover, move the date slider or play the sequence. Axes are fixed across frames; the surface between integer ranks is visual interpolation. A peak is not a crash probability or a trade recommendation. Numerical frame/configuration verification does not imply browser interaction was tested here.
    ''')
    code('''
    explorer = output / "topology/Final-Test-Landscape-Explorer.html"
    figure = json.loads((output / "topology/explorer-figure.json").read_text())
    assert len(figure["frames"]) == 72
    assert len(figure["layout"]["sliders"][0]["steps"]) == 72
    print("Frames:", len(figure["frames"]), "from", figure["frames"][0]["name"], "to", figure["frames"][-1]["name"])
    display(Markdown("[Open the offline final-test 3D companion](../outputs/final/topology/Final-Test-Landscape-Explorer.html)"))
    ''')
    md('''
    ## 8. Record the setbacks and stop selecting on this test

    The decision log covers all five milestones. This stage records the no-overlay fork, adjusted-price vintage audit, absolute-versus-relative inference, failed economic evidence conditions, poor topology-model transfer and the empty-ledger repair. The negative hypothesis remains negative.

    The research evaluation is complete for this design. The next milestone prepares the public repository and accurate CV/LinkedIn presentation, with the final PDF waiting for the author's style specification. Any future strategy revision requires new evidence; this period is permanently observed.
    ''')
    code('''
    decision_log = (ROOT / "docs/milestone-decisions.md").read_text()
    for milestone in range(1,6):
        assert f"## Milestone {milestone}" in decision_log
    assert manifest["test_is_now_observed"] and not manifest["post_test_model_selection"]
    assert not any(manifest["evidence_gate"]["conditions"].values())
    print("Problem-solving records cover all five completed milestones.")
    print("No primary-model retuning. Final test now observed. Final PDF deferred.")
    ''')
    md('''
    ## 9. Run the focused engineering checks

    The suite checks causal execution, ledger accounting, numerical projection, graph and persistence relationships, paired uncertainty, vintage comparisons and the evidence gate. A passing engineering check establishes none of the economic claims by itself.
    ''')
    code('''
    import subprocess
    check = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=ROOT, capture_output=True, text=True)
    log = check.stdout + check.stderr
    (ROOT / "validation/milestone-5-tests.txt").write_text(log)
    print(log)
    assert check.returncode == 0
    ''')
    refs=json.loads((ROOT/'paper/references.json').read_text())
    selected=[5,9,10,16,17,18,21,22,23,24]
    bibliography=sorted([harvard_reference(r) for r in refs if r['id'] in selected],key=lambda s:s.split(' (')[0].casefold())
    md('## References\n\n'+'\n\n'.join(bibliography))
    n=nbformat.v4.new_notebook(cells=cells,metadata={
        'milestone':5,'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.12.14'}})
    nbformat.validate(n)
    nbformat.write(n,ROOT/'notebooks/05-final-evaluation.ipynb')
    print('Created fifth notebook with',sum(c.cell_type=='code' for c in cells),'code cells.')


if __name__=='__main__':
    main()
