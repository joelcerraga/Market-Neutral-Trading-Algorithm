"""Verify saved research evidence, including repaired outputs and interactive data."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import json
import re
import sys
import numpy as np
import pandas as pd
import nbformat
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from market_neutral.config import ResearchConfig
from market_neutral.historical import sha256
from market_neutral.comparison import validate_ledger
from market_neutral.final_data import load_final_protocol
from market_neutral.final_inference import CONTRASTS, evidence_gate


def verify():
    p=load_final_protocol(ROOT)
    out=ROOT/'outputs/final'
    manifest=json.loads((out/'run-manifest.json').read_text())
    locked=json.loads((ROOT/'data/final-snapshot.lock.json').read_text())
    assert sha256(ROOT/'data/final-processed/adjusted-prices.csv') == locked['input_sha256'] == manifest['input_sha256']
    for name,expected in manifest['files'].items():
        assert (out/name).stat().st_size > 0, name
        assert sha256(out/name) == expected, name
    for name,expected in manifest['source_sha256'].items():assert sha256(ROOT/name)==expected,name
    for ticker in [t for group in p['universe'].values() for t in group]+[p['benchmark']]:
        for folder in ['data/cache',p['cache']]:
            path=ROOT/folder/f'{ticker}.csv'
            assert sha256(path)==json.loads(path.with_suffix('.json').read_text())['csv_sha256']
    audit=pd.read_csv(out/'data-audit.csv')
    assert len(audit)==25 and audit.rows.eq(1761).all() and audit.overlap_returns.eq(252).all()
    assert audit[['missing','nonpositive_volume','moves_above_40pct']].eq(0).all().all()
    assert audit.max_abs_overlap_return_change.max() <= p['data_review']['overlap_max_abs_daily_return_difference']
    lock=json.loads((ROOT/'protocol/final-evaluation-v1.lock.json').read_text())
    release=json.loads((out/'holdout-release.json').read_text())
    downloads=json.loads((ROOT/'data/final-download-manifest.json').read_text())
    assert pd.Timestamp(lock['locked_utc']) < pd.Timestamp(release['release_started_utc'])
    assert all(pd.Timestamp(release['release_started_utc']) < pd.Timestamp(f['retrieved_utc']) for f in downloads['files'])
    summary=pd.read_csv(out/'final-summary.csv')
    experiments=json.loads((out/'experiment-register.json').read_text())
    expected={(m,fee,.02) for m in ['baseline','graph_tau_0.5','graph_tau_1','graph_tau_2'] for fee in [0,5,10,20]}
    expected|={(m,5,b) for m in ['baseline','graph_tau_1'] for b in [0,.05]}
    expected|={(m,5,.02) for m in ['baseline_matched','graph_matched']}
    actual=set(zip(summary.model,summary.trading_cost_bps,summary.annual_borrow_rate))
    assert actual==expected and len(summary)==len(experiments)==22
    all_dates=None;ledgers={}
    for entry in experiments:
        ledger=pd.read_csv(out/entry['ledger'],index_col='date',parse_dates=True)
        assert len(ledger)==1508 and np.isfinite(ledger.to_numpy()).all()
        assert ledger.index.is_unique and ledger.index.is_monotonic_increasing
        assert ledger.index[0]==pd.Timestamp('2020-01-02') and ledger.index[-1]==pd.Timestamp('2025-12-31')
        if all_dates is None:all_dates=ledger.index
        assert ledger.index.equals(all_dates)
        config=ResearchConfig(**entry['configuration'])
        validate_ledger(SimpleNamespace(ledger=ledger),config)
        assert (ledger.nav>0).all()
        # Reconstruct saved dollars and summary values independently of in-memory results.
        previous_nav=np.r_[config.initial_capital,ledger.nav.to_numpy()[:-1]]
        np.testing.assert_allclose(ledger.nav,previous_nav*(1+ledger.net_return),atol=1e-6,rtol=1e-10)
        np.testing.assert_allclose(ledger.trading_cost,ledger.trading_cost_return*previous_nav,atol=1e-7)
        np.testing.assert_allclose(ledger.borrow_cost,ledger.borrow_cost_return*previous_nav,atol=1e-7)
        np.testing.assert_allclose(ledger.trading_cost,ledger.traded_notional*config.trading_cost_bps/10000,atol=1e-7)
        selected=summary.loc[(summary.model==entry['model']) & (summary.trading_cost_bps==config.trading_cost_bps) &
                             (summary.annual_borrow_rate==config.annual_borrow_rate)]
        assert len(selected)==1
        row=selected.iloc[0];growth=(1+ledger.net_return).prod()
        np.testing.assert_allclose([growth-1,growth**(252/len(ledger))-1,252*ledger.net_return.mean()],
                                  [row.total_return,row.annualised_return,row.annualised_arithmetic_net],atol=1e-10)
        np.testing.assert_allclose(row.annualised_arithmetic_net,
            row.annualised_arithmetic_gross-row.annualised_trading_drag-row.annualised_borrow_drag,atol=1e-11)
        ledgers[entry['id']]=ledger
    annual=pd.read_csv(out/'calendar-year-results.csv')
    assert len(annual)==12 and set(annual.year)==set(range(2020,2026))
    for model in ['baseline','graph_tau_1']:
        ledger=ledgers[f'final_test__{model}__fee5__borrow0.02']
        rows=annual.loc[annual.model==model]
        assert rows.days.sum()==1508
        for _,row in rows.iterrows():
            part=ledger.loc[ledger.index.year==row.year]
            assert len(part)==row.days
            np.testing.assert_allclose((1+part.net_return).prod()-1,row.net_return,atol=1e-11)
    assert annual.net_return.lt(0).all()
    weights={}
    for path in out.glob('*-weights.csv'):
        w=pd.read_csv(path,index_col=0,parse_dates=True)
        assert len(w)==1508 and w.index.equals(all_dates)
        assert np.isfinite(w.to_numpy()).all()
        assert w.sum(axis=1).abs().max()<1e-10
        assert w.abs().max().max()<=.08+1e-10 and w.abs().sum(axis=1).max()<=1+1e-10
        assert w.iloc[-1].eq(0).all()
        weights[path.stem.replace('-weights','')]=w
    assert len(weights)==6
    np.testing.assert_allclose(weights['baseline_matched'].abs().sum(axis=1),
                               weights['graph_matched'].abs().sum(axis=1),atol=1e-10)
    paired=pd.read_csv(out/'paired-returns.csv',index_col=0,parse_dates=True)
    np.testing.assert_allclose(paired.difference,paired.graph-paired.baseline,atol=2e-13)
    intervals=pd.read_csv(out/'mean-inference.csv')
    assert len(intervals)==24 and set(intervals.contrast)==set(CONTRASTS)
    assert not intervals.duplicated(['contrast','method','block_or_lags','interval_type']).any()
    for _,group in intervals.groupby(['contrast','method','block_or_lags']):
        g=group.set_index('interval_type')
        assert set(g.index)=={'pointwise','bonferroni'}
        np.testing.assert_allclose(g.loc['pointwise','confidence_level'],.95)
        np.testing.assert_allclose(g.loc['bonferroni','confidence_level'],1-.05/3)
        assert g.loc['bonferroni','annualised_lower']<=g.loc['pointwise','annualised_lower']
        assert g.loc['bonferroni','annualised_upper']>=g.loc['pointwise','annualised_upper']
    samples=pd.read_csv(out/'primary-bootstrap-means.csv')
    assert len(samples)==10000
    np.testing.assert_allclose(samples[CONTRASTS[2]],samples[CONTRASTS[1]]-samples[CONTRASTS[0]],atol=2e-14)
    for contrast in CONTRASTS:
        g=intervals.loc[(intervals.contrast==contrast)&(intervals.method=='stationary bootstrap')&(intervals.block_or_lags==10)]
        for _,row in g.iterrows():
            tail=(1-row.confidence_level)/2
            np.testing.assert_allclose(252*np.quantile(samples[contrast],[tail,1-tail]),
                                      [row.annualised_lower,row.annualised_upper],atol=1e-10)
    control=pd.read_csv(out/'matched-uncertainty.csv');assert len(control)==2
    graph=summary.loc[(summary.model=='graph_tau_1')&(summary.purpose=='primary')].iloc[0]
    gate=evidence_gate(graph.annualised_return,intervals,control)
    assert gate==manifest['evidence_gate'] and not any(gate['conditions'].values())
    repair=json.loads((ROOT/'validation/final-artifact-repair.json').read_text())
    initial=json.loads((ROOT/'validation/final-initial-run-manifest.json').read_text())
    assert repair['status']=='verified' and repair['repaired_rows']==1508
    for name,expected_hash in initial['files'].items():
        if name!=repair['affected_output']:assert manifest['files'][name]==expected_hash,name
    assert sha256(out/repair['affected_output'])==repair['repaired_sha256']!=repair['initial_sha256']
    topology=out/'topology'
    features=pd.read_csv(topology/'features.csv',index_col='date',parse_dates=True)
    assert len(features)==4524 and np.isfinite(features.to_numpy()).all()
    for window in p['topology_transfer']['windows']:
        assert features.loc[features.window==window].index.equals(all_dates)
    assert features.essential_h0.eq(1).all() and features.finite_h0.eq(23).all()
    assert features.zero_h0_merges.eq(0).all()
    for name,count in [('control-correlations.csv',36),('control-model-scores.csv',12),
                       ('window-sensitivity.csv',8),('diagram-stability.csv',288)]:
        assert len(pd.read_csv(topology/name))==count,name
    checks=pd.read_csv(topology/'diagram-stability.csv')
    assert (checks.bottleneck_distance<=checks.max_distance_change+2e-6).all()
    assert not manifest['topology']['control_models_refitted']
    assert sha256(ROOT/'outputs/topology/control-models.json')==p['topology_control_models_sha256']
    pngs={}
    for path in sorted(out.glob('*.png')):
        with Image.open(path) as im:size=im.size;im.verify()
        assert min(size)>=500 and path.stat().st_size>1000
        pngs[path.name]={'pixels':size,'sha256':sha256(path)}
    assert len(pngs)==4
    fig=json.loads((topology/'explorer-figure.json').read_text())
    snapshots=json.loads((topology/'monthly-diagrams.json').read_text())
    assert len(fig['frames'])==72 and len(snapshots)==216
    steps=fig['layout']['sliders'][0]['steps']
    assert len(steps)==72 and len(fig['layout']['updatemenus'][0]['buttons'])==2
    assert [s['label'] for s in steps]==[f['name'] for f in fig['frames']]
    assert [s['args'][0][0] for s in steps]==[f['name'] for f in fig['frames']]
    for frame in fig['frames']:
        snapshot=snapshots[frame['name']+'|126']
        bars=np.asarray(snapshot['h1']).reshape(-1,2)
        x=np.asarray(frame['data'][0]['x']);layers=np.asarray(frame['data'][0]['z'])
        assert layers.shape==(5,401) and np.all(layers>=0)
        for j,threshold in enumerate(x):
            ordered=sorted([max(0.,min(threshold-b,d-threshold)) for b,d in bars],reverse=True)
            np.testing.assert_allclose(layers[:,j],(ordered+[0.]*5)[:5],atol=1e-14)
        np.testing.assert_allclose(frame['data'][1]['x'],bars[:,0])
        np.testing.assert_allclose(frame['data'][1]['y'],bars[:,1])
        assert layers.max()<=fig['layout']['scene']['zaxis']['range'][1]
    html=(topology/'Final-Test-Landscape-Explorer.html').read_text()
    assert 'Plotly.addFrames' in html and 'plotly.js' in html and '<h2>References</h2>' in html
    assert not re.search(r'<script\b[^>]*\bsrc=',html,re.I)
    manuscript=(ROOT/'paper/manuscript.md').read_text()
    prose=re.sub(r'```.*?```','',manuscript,flags=re.S)
    assert not re.search(r'\[\d+\]',prose) and '<!--' not in manuscript
    counts={}
    for kind,count in [('Equation',30),('Table',27),('Listing',15)]:
        numbers=[int(n) for n in re.findall(rf'^{kind} (\d+)\.',manuscript,flags=re.M)]
        assert numbers==list(range(1,count+1)),(kind,numbers)
        counts[kind.lower()]=count
    figure_links=re.findall(r'!\[Figure (\d+)\. [^\]]+\]\(([^)]+)\)',manuscript)
    assert [int(n) for n,_ in figure_links]==list(range(1,17))
    for _,path in figure_links:
        with Image.open((ROOT/'paper'/path).resolve()) as im:im.verify()
    counts['figure']=16
    bibliography=manuscript.split('## References\n\n',1)[1].strip()
    assert bibliography==(ROOT/'paper/references-harvard.md').read_text().strip()
    references=bibliography.split('\n\n');assert len(references)==24
    assert references==sorted(references,key=lambda s:s.split(' (')[0].casefold())
    for entry in references:
        assert re.match(r'[A-Z][^\n]+\(\d{4}[ab]?\) ',entry)
        assert not any(term in entry for term in ['Primary source','Primary data','Not a scientific paper','Evidence:'])
    notebooks={}
    for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
        n=nbformat.read(path,as_version=4);nbformat.validate(n)
        codes=[c for c in n.cells if c.cell_type=='code']
        assert all(c.execution_count is not None for c in codes)
        assert not any(o.output_type=='error' for c in codes for o in c.outputs)
        refs=[c for c in n.cells if c.cell_type=='markdown' and c.source.startswith('## References\n')]
        assert len(refs)==1
        notebooks[path.name]={'executed_code_cells':len(codes),'error_outputs':0}
    assert len(notebooks)==5 and notebooks['05-final-evaluation.ipynb']['executed_code_cells']==10
    tests=(ROOT/'validation/milestone-5-tests.txt').read_text()
    assert re.search(r'Ran 41 tests in ',tests) and tests.rstrip().endswith('OK')
    decisions=(ROOT/'docs/milestone-decisions.md').read_text()
    assert all(f'## Milestone {n}' in decisions for n in range(1,6))
    record={'verified_utc':datetime.now(timezone.utc).isoformat(),'status':'passed',
        'final_scenarios':22,'sessions_per_ledger':1508,'saved_ledgers_reconciled':22,
        'numerical_output_hashes_verified':len(manifest['files']),
        'unaffected_initial_hashes_reproduced':repair['unaffected_hashes_reproduced'],
        'artifact_repair':'verified; initial manifest retained','feature_rows':4524,
        'diagram_bound_checks':288,'interactive_frames':72,'landscape_samples_verified':72*5*401,
        'slider_dates_match_frames':True,'pngs':pngs,'manuscript_counts':counts,'harvard_references':24,
        'notebooks':notebooks,'focused_tests':41,'decision_log_milestones':[1,2,3,4,5],
        'pdf_compiled':False,'final_test_now_observed':True,'post_test_model_selection':False,
        'evidence_conditions_met':sum(gate['conditions'].values()),
        'protocol_sha256':manifest['protocol_sha256'],'input_sha256':manifest['input_sha256'],
        'browser_interaction':'Not executed here; frame values and control configuration verified'}
    (ROOT/'validation/milestone-5-artifacts.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':verify()
