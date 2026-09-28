"""Historical-data boundaries and parser checks independent of network availability."""
import unittest
import numpy as np
import pandas as pd
from dataclasses import replace
from market_neutral.config import ResearchConfig
from market_neutral.data import generate_synthetic,simple_returns
from market_neutral.historical import phase_inputs,parse_chart,baseline_decisions
from market_neutral.strategy import build_decisions


class HistoricalChecks(unittest.TestCase):
    def setUp(self):
        self.dates=pd.bdate_range('2019-12-23',periods=8)
        self.r=pd.DataFrame({'A':np.arange(8)/1000},index=self.dates)
        self.w=pd.DataFrame({'A':np.arange(8)/100},index=self.dates)
        self.b=self.w*0+1
        self.p={'allowed_phases':['development'],'phases':{'development':['2019-12-26','2019-12-31'],'final_holdout':['2020-01-01','2025-12-31']}}

    def test_shift_precedes_phase_slicing(self):
        r,w,b=phase_inputs(self.r,self.w,self.b,self.p,'development')
        date=r.index[0];position=self.r.index.get_loc(date)
        self.assertEqual(w.iloc[0,0],self.w.iloc[position-1,0])
        self.assertLess(r.index.max(),pd.Timestamp('2020-01-01'))

    def test_reserved_phase_is_refused(self):
        with self.assertRaisesRegex(ValueError,'reserved'):
            phase_inputs(self.r,self.w,self.b,self.p,'final_holdout')

    def payload(self):
        timestamps=[int(pd.Timestamp(d+' 14:30',tz='UTC').timestamp()) for d in ['2019-12-30','2019-12-31']]
        return {'chart':{'result':[{'meta':{'symbol':'AAPL','currency':'USD','regularMarketPrice':9999},'timestamp':timestamps,'indicators':{'quote':[{'close':[10.,11.],'volume':[100,100]}],'adjclose':[{'adjclose':[9.,10.]}]}}],'error':None}}

    def test_parser_uses_adjusted_price_and_strips_current_quote(self):
        frame,meta=parse_chart(self.payload(),'AAPL','2019-01-01','2020-01-01')
        self.assertEqual(frame.adjclose.tolist(),[9,10])
        self.assertNotIn('regularMarketPrice',meta)

    def test_parser_rejects_future_bar_and_missing_adjusted_close(self):
        payload=self.payload()
        payload['chart']['result'][0]['timestamp'][-1]=int(pd.Timestamp('2020-01-02 14:30',tz='UTC').timestamp())
        with self.assertRaisesRegex(ValueError,'outside'):
            parse_chart(payload,'AAPL','2019-01-01','2020-01-01')
        payload=self.payload();payload['chart']['result'][0]['indicators'].pop('adjclose')
        with self.assertRaisesRegex(ValueError,'adjusted'):
            parse_chart(payload,'AAPL','2019-01-01','2020-01-01')

    def test_historical_baseline_preserves_milestone_one_rule(self):
        cfg=ResearchConfig(observations=70,assets=8,sectors=2,correlation_window=20,beta_window=20,volatility_window=15,neighbours=2)
        r,m=simple_returns(generate_synthetic(cfg))
        w,b=baseline_decisions(r,m,cfg)
        original=build_decisions(r,m,cfg)
        np.testing.assert_allclose(w,original.targets['baseline'],atol=1e-12)
        np.testing.assert_allclose(b,original.betas,equal_nan=True,atol=1e-12)


if __name__=='__main__':unittest.main()
