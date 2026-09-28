## 13. Conclusion and future work

### 13.1. Conclusion

The objective of this project was to develop and evaluate a market-neutral trading framework that uses relationships between stock returns while accounting explicitly for costs and market exposure. The implementation objective was achieved: the completed Python framework integrates a reversal baseline, graph diffusion, constrained portfolio formation, delayed execution, a reconciled cost ledger, dependence-aware uncertainty and persistent-homology diagnostics. The financial objective was not demonstrated. Under the fixed universe and stated costs, the proposed graph strategy does not establish profitable or reliably superior performance.

The final 2020–2025 evaluation is the decisive comparison for the frozen design. At 5 basis points per dollar traded and 2% annual short borrow, baseline CAGR is −5.57% and primary graph CAGR is −4.80%. The graph's annualised arithmetic improvement of +0.73 percentage points has an adjusted interval spanning −2.14 to +3.85 percentage points. Matched-gross results also leave the direction of the improvement unresolved. None of the four necessary evidence conditions specified before final-data acquisition is met. The smaller observed loss must therefore be reported as a descriptive finding, rather than evidence of profitable alpha.

The topology study contributes a separate result. Persistent homology can be computed causally and checked against known mathematical relationships, but additional mathematical structure does not automatically create additional financial value. H0 substantially overlaps a simpler correlation measure, while H1 is sensitive to the estimation horizon and some descriptive models transfer poorly. Retaining those limitations and declining to add an unsupported trading overlay are part of the research outcome.

The project also demonstrates how setbacks can improve the quality of an investigation without changing an unsuccessful hypothesis into a successful one. Exposure differences motivated a matched-gross control; serial dependence motivated paired uncertainty procedures; revised adjusted-price histories motivated a return-overlap audit; and failed output and slider checks motivated verified persistence and explicit interactive-calendar validation. These responses make the analysis more transparent and reproducible. They do not remove the negative economic finding or the limits of the data.

Accordingly, the final contribution is an auditable quantitative research process: established relationships are attributed, project choices are declared, every planned scenario is retained, and conclusions follow the evidence. The combination of mathematical derivation, executable code, diagnostic figures and a documented decision record provides a foundation for further research, while keeping the boundary between engineering correctness and investment performance explicit.

### 13.2. Future work

The first priority for a stronger financial study is a point-in-time universe with delisting outcomes, a more complete corporate-action record and historical borrowing information. Those observations would permit a broader assessment of sample validity and implementability. They should be acquired and audited before selecting additional model complexity.

A separate experiment could investigate whether a slower rebalancing schedule or an explicit trading threshold improves the relationship between gross contribution and recurring costs. Such a change must be specified before examining newly reserved observations, with the original baseline retained and the full candidate set reported. The current final period cannot be reused as an untouched test for that choice.

Any future use of topology should begin with a precise economic hypothesis, a stated feature direction and a training-only rule. It should then be compared with ordinary correlation and volatility controls under the same timing, exposure and cost conventions. Persistent-homology computation alone is insufficient justification for a trading overlay.

The remaining presentation work is to publish the reproducible source structure and interactive companions with accurate CV and LinkedIn descriptions. Those descriptions should emphasise implementation, empirical testing, mathematical verification and the retained negative result. A claim of demonstrated profitable alpha would go beyond the evidence established by this project.
