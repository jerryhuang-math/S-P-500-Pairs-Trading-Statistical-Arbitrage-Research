import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import joint_grid_search as grid


class GridTests(unittest.TestCase):
    def fixture(self):
        dates = pd.bdate_range('2020-01-02', periods=12)
        z = np.array([-2.5, -2.5, -1, 0, 2.5, 2.5, 3.5, 3.5, 0, -2.5, -2.5, 0])
        prices = pd.DataFrame({'A': 100 * np.exp(z * .01), 'B': 100.}, index=dates)
        pair = {'A': 'A', 'B': 'B', 'Alpha': 0., 'Beta': 1., 'Spread Mean': 0., 'Spread Std': .01,
                'Ticker 1': 'A', 'Ticker 2': 'B', 'Correlation': .85, 'Status': 'OK',
                'EG Statistic': -4., 'EG p-value': .02,
                'EG 1% Critical Value': -4.5, 'EG 5% Critical Value': -3.5}
        seed = pd.Series({'A': 100., 'B': 100.}, name=dates[0] - pd.Timedelta(days=1))
        return dates, prices, pair, seed

    def test_grid(self):
        params = grid.parameter_grid()
        self.assertEqual(len(params), 1248)
        self.assertEqual(len({grid.parameter_id(p) for p in params}), 1248)
        self.assertTrue(all(p['trading_months'] <= p['formation_months'] for p in params))
        schedules = [grid.make_windows(grid.DATA_START, grid.HOLDOUT_START, f, t, t, grid.COMMON_START)
                     for f in grid.FORMATION_GRID for t in grid.TRADING_GRID if t <= f]
        for schedule in schedules:
            self.assertEqual(schedule.iloc[0]['Trading Start'], grid.COMMON_START)
            self.assertEqual(schedule.iloc[-1]['Trading End Exclusive'], grid.HOLDOUT_START)
            self.assertTrue((schedule['Formation Start'] >= grid.DATA_START).all())

    def test_scaling_and_execution(self):
        dates, prices, pair, seed = self.fixture()
        for z in grid.Z_GRID:
            direct = grid.backtest_pair(pair, prices, seed, 12345., 5.,
                                       entry_z=z[0], exit_z=z[1], stop_z=z[2])
            unit = grid.backtest_pair(pair, prices, seed, 1., 5.,
                                     entry_z=z[0], exit_z=z[1], stop_z=z[2])
            scaled = grid.scale_result(unit, 12345.)
            for a, b in zip(direct, scaled):
                pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-9, atol=1e-8)
        daily, trades = grid.backtest_pair(pair, prices, seed, 1000., 5.)
        self.assertEqual(trades.iloc[0]['Entry Date'], dates[1])
        self.assertTrue(daily.iloc[-1]['Position'] == 0)

    def test_selection(self):
        _, _, pair, _ = self.fixture()
        reverse = pair | {'A': 'B', 'B': 'A', 'EG Statistic': -5., 'EG p-value': .001}
        directions = pd.DataFrame([pair, reverse])
        self.assertEqual(grid.GridSearch.select(directions, .8, .01).iloc[0]['A'], 'B')
        self.assertTrue(grid.GridSearch.select(directions, .9, .05).empty)
        self.assertTrue(grid.GridSearch.select(pd.DataFrame([pair]), .8, .01).empty)
        self.assertEqual(len(grid.GridSearch.select(pd.DataFrame([pair]), .8, .05)), 1)

    def test_exports_resume_no_trades(self):
        for cost_bps in (5., 0.):
            with self.subTest(cost_bps=cost_bps):
                self.check_exports_resume_no_trades(cost_bps)

    def check_exports_resume_no_trades(self, cost_bps):
        dates, prices, pair, seed = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            search = grid.GridSearch.__new__(grid.GridSearch)
            search.folder = Path(tmp)
            search.prices = prices
            search.treasury_yields = pd.Series(5., index=pd.date_range('2019-12-20', dates[-1]))
            search.cost_bps, search.initial_capital, search.run_id = cost_bps, 10000., 'fixture'
            window = {'Window': 1, 'Formation Start': pd.Timestamp('2019-01-01'),
                'Formation End Exclusive': dates[0], 'Trading Start': dates[0],
                'Trading End Exclusive': dates[-1] + pd.Timedelta(days=1), 'Shortened': True}
            cached = {'directions': pd.DataFrame([pair]), 'formation_last': seed,
                      'eligibility': pd.DataFrame({'Eligible': [True, True]})}
            search.schedule = lambda f, t: pd.DataFrame([window])
            search.formation = lambda w: cached
            search.trading_prices = lambda tickers, ds: prices.reindex(index=ds, columns=tickers)
            with patch.object(grid, 'COMMON_START', dates[0]):
                result = search.run(max_workers=1, window_settings=[(3, 2)], z_values=[(1.5, .5, 3.)])
                complete = result.loc[result.Status == 'complete']
                self.assertEqual(len(complete), 4)
                self.assertEqual((complete['Number of Trades'] == 0).sum(), 3)
                for _, row in complete.iterrows():
                    folder = Path(row['Output Folder'])
                    pd.read_csv(folder / 'pair_daily.csv.gz')
                    trades = pd.read_csv(folder / 'trades.csv')
                    daily = pd.read_csv(folder / 'portfolio_daily.csv')
                    if cost_bps == 0:
                        self.assertTrue(daily['Costs ($)'].eq(0).all())
                        np.testing.assert_allclose(daily['Equity'], daily['Gross Equity'])
                        self.assertTrue(trades['Costs ($)'].eq(0).all())
                    else:
                        np.testing.assert_allclose(daily['Costs ($)'],
                                                   daily['Traded Value ($)'] * cost_bps / 10000)
                    if len(trades):
                        self.assertTrue(set(grid.EXTRA_TRADE_COLUMNS).issubset(trades.columns))
                        self.assertTrue(trades['Units A'].notna().all())
                mtimes = {p: p.stat().st_mtime_ns for p in Path(tmp).glob('*/summary.csv')}
                search.formation = lambda w: (_ for _ in ()).throw(AssertionError('Must skip completed batch'))
                search.run(max_workers=1, window_settings=[(3, 2)], z_values=[(1.5, .5, 3.)])
                self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in mtimes})

    def test_holdout_ingestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'A.csv'
            path.write_text(f'Date,Adj Close\n2020-01-02,100\n{grid.HOLDOUT_START:%Y-%m-%d},BAD\n')
            self.assertEqual(list(grid.read_training_series(path)), [100.])


if __name__ == '__main__':
    unittest.main()
