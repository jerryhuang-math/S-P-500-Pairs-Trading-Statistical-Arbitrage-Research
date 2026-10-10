import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from risk_free import annualized_treasury_return
from joint_grid_search import performance_metrics, combine_accounts, TRADE_COLUMNS


class TreasuryTests(unittest.TestCase):
    def test_constant_yield_and_period_specific_compounding(self):
        dates = pd.bdate_range('2020-01-02', periods=504)
        yields = pd.Series(5., index=pd.date_range('2019-12-20', dates[-1]))
        self.assertAlmostEqual(annualized_treasury_return(dates, yields), .05)
        self.assertAlmostEqual(annualized_treasury_return(dates[:20], yields), .05)
        yields.loc['2021-01-01':] = 2.
        prior = yields.reindex(dates - pd.Timedelta(days=1), method='ffill') / 100
        expected = np.prod((1 + prior.to_numpy()) ** (1 / 252)) ** (252 / len(dates)) - 1
        self.assertAlmostEqual(annualized_treasury_return(dates, yields), expected)
        self.assertNotAlmostEqual(annualized_treasury_return(dates[:20], yields),
                                  annualized_treasury_return(dates[-20:], yields))

    def test_lag_holidays_and_missing_coverage(self):
        yields = pd.Series([4., 90.], index=pd.to_datetime(['2020-01-03', '2020-01-06']))
        self.assertAlmostEqual(annualized_treasury_return(pd.to_datetime(['2020-01-06']), yields), .04)
        for day in ['2019-12-31', '2020-01-15']:
            with self.assertRaisesRegex(ValueError, 'coverage'):
                annualized_treasury_return(pd.to_datetime([day]), yields)

    def test_both_engines_formula_and_zero_volatility(self):
        notebook = json.loads((ROOT / 'notebooks/03_pair_selection_first_result.ipynb').read_text())
        cell = next(''.join(c['source']) for c in notebook['cells']
                    if 'def performance_metrics(' in ''.join(c['source']))
        namespace = dict(np=np, pd=pd, TRADING_DAYS=252,
                         annualized_treasury_return=annualized_treasury_return)
        exec(compile(cell, 'notebook03_metrics', 'exec'), namespace)
        dates = pd.bdate_range('2020-01-02', periods=20)
        yields = pd.Series(5., index=pd.date_range('2019-12-20', dates[-1]))
        trades = pd.DataFrame(columns=TRADE_COLUMNS)
        daily = combine_accounts([], dates, 1000.)
        for function in [performance_metrics, namespace['performance_metrics']]:
            self.assertTrue(np.isnan(function(daily, trades, 1000., yields)['Sharpe Ratio']))
        returns = np.tile([.002, -.001], 10)
        daily['Net Return'] = returns
        daily['Equity'] = 1000 * (1 + returns).cumprod()
        daily['Gross Equity'] = daily['Equity']
        expected_return = ((1 + returns).prod()) ** (252 / len(returns)) - 1
        expected_volatility = returns.std(ddof=1) * np.sqrt(252)
        for function in [performance_metrics, namespace['performance_metrics']]:
            result = function(daily, trades, 1000., yields)
            self.assertAlmostEqual(result['Annualized Risk-Free Return'], .05)
            self.assertAlmostEqual(result['Sharpe Ratio'], (expected_return - .05) / expected_volatility)


if __name__ == '__main__':
    unittest.main()
