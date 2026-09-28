## 11. Setbacks, design forks and their treatment

The project records methodological forks, observed empirical setbacks and implementation failures separately. A design safeguard is not described as a bug that occurred. The detailed record in `docs/milestone-decisions.md` identifies the evidence, response and unresolved limitation for every completed milestone. The Milestone 1–3 entries are retrospective summaries of retained artifacts; the Milestone 4 and 5 entries were written during their respective work.

Table 26. Problem-solving record across completed milestones

| Milestone | Setback or fork | Response and remaining limit |
| --- | --- | --- |
| 1. Foundations | Synthetic mean reversion favours the intended signal; exposure and timing conventions need explicit decisions | Treat synthetic returns as engine checks; test projection, delayed execution, drift costs and terminal liquidation; real-market usefulness remains untested at this stage |
| 2. Historical baseline | Available data omit a point-in-time universe; default-cost returns are negative | Label the survivor-basket scope, preserve source hashes and every fee case; no stock/date substitution; survivorship bias and profitability remain unresolved |
| 3. Graph comparison | Equal exposure ceilings yield different actual gross; the apparent validation gain is uncertain | Add declared matched-gross controls and dependent-return intervals; retain the negative development result and confidence interval spanning zero |
| 4. Topology | H0 overlaps simple correlation; H1 is window-sensitive; an H0 control relation transfers poorly | Keep simple controls, all windows and negative R²; do not choose a favourable setting or introduce an untested overlay; numerical verification is complete but financial usefulness remains open |
| 5. Final evaluation | Default-cost losses persist; paired improvement is uncertain; some topology/control relations fail to transfer; one saved ledger was empty | Lock criteria before acquisition; retain all cases and negative findings; repair output writes and reproduce unaffected hashes; the test is now observed |

The first final run also exposed a persistence failure: one sensitivity ledger was empty despite a completed in-memory calculation. The original manifest is retained. Verified atomic writes and a full replay repair the artifact, with every unaffected numerical-output hash required to match and every saved ledger checked against its original summary. The exact cause of the original write failure was not established. A separate notebook assertion found stale slider entries left by an array merge in the reused 3D layout. Explicit slider replacement and exact frame/slider calendar checks repaired that defect; live browser interaction remains a separate local check.

The mitigation is not always a successful new model. For the historical losses and unstable feature relationships, the appropriate response is to narrow the claim, preserve the evidence and state the next decision explicitly. As White (2000) explains in *A Reality Check for Data Snooping*, searching many alternatives complicates interpretation; as Bailey et al. (2017) discuss in *The probability of backtest overfitting*, a final holdout alone does not erase that search. The protocol history therefore remains part of the final research narrative.
