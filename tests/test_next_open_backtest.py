import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from next_open_backtest import adjusted_open, backtest_pair_next_open
from joint_grid_search import backtest_pair


class NextOpenTests(unittest.TestCase):
    def fixture(self):
        dates = pd.bdate_range('2020-01-02', periods=6)
        close = pd.DataFrame({'A': 100 * np.exp(np.array([2., .2, 0., -2., -.2, 0.]) * .01),
                              'B': 100.}, index=dates)
        pair = {'A': 'A', 'B': 'B', 'Beta': 1., 'Spread Mean': 0., 'Spread Std': .01}
        seed = pd.Series({'A': 100., 'B': 100.}, name=dates[0] - pd.Timedelta(days=1))
        return close, pair, seed

    def test_adjustment_preserves_intraday_ratio(self):
        frame = pd.DataFrame({'Open': [100., 25.], 'Close': [110., 26.], 'Adj Close': [55., 26.]})
        np.testing.assert_allclose(adjusted_open(frame), [50., 25.])
        np.testing.assert_allclose(adjusted_open(frame) / frame['Adj Close'], frame['Open'] / frame['Close'])
        frame.loc[0, 'Close'] = 0
        with self.assertRaises(ValueError):
            adjusted_open(frame)

    def test_identical_fills_reproduce_baseline_with_costs(self):
        close, pair, seed = self.fixture()
        expected = backtest_pair(pair, close, seed, 10000., 5., entry_z=1.5, exit_z=.5, stop_z=4.)
        actual = backtest_pair_next_open(pair, close, close, seed, 10000., 5., entry_z=1.5, exit_z=.5, stop_z=4.)
        for left, right in zip(expected, actual):
            pd.testing.assert_frame_equal(left, right)

    def test_entry_uses_prior_close_and_marks_current_close(self):
        close, pair, seed = self.fixture()
        opening = close.copy()
        opening.iloc[1, 0] = 101.
        daily, trades = backtest_pair_next_open(pair, close, opening, seed, 10000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        first = trades.iloc[0]
        self.assertEqual(first['Entry Signal Date'], close.index[0])
        self.assertEqual(first['Entry Date'], close.index[1])
        self.assertAlmostEqual(first['Entry z'], np.log(101 / 100) / .01)
        expected_mark = 10000. + (-5000 / 101) * (close.iloc[1, 0] - 101.)
        self.assertAlmostEqual(daily.iloc[1]['Equity'], expected_mark)
        np.testing.assert_allclose(trades['Net P/L ($)'].sum(), daily.Equity.iloc[-1] - 10000.)
        # Change today's close: today's opening holdings must stay unchanged.
        changed = close.copy()
        changed.iloc[1, 0] = 105.
        other, _ = backtest_pair_next_open(pair, changed, opening, seed, 10000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        self.assertEqual(daily.iloc[1]['Units A'], other.iloc[1]['Units A'])

    def test_stop_blacklists_and_window_end_closes_at_close(self):
        close, pair, seed = self.fixture()
        close['A'] = 100 * np.exp(np.array([2., 5., 0., 2., 2., 2.]) * .01)
        opening = close.copy()
        opening.iloc[2, 0] = 106.
        daily, trades = backtest_pair_next_open(pair, close, opening, seed, 10000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades.iloc[0]['Exit Reason'], 'Stop loss')
        self.assertEqual(trades.iloc[0]['Exit Date'], close.index[2])
        self.assertTrue(daily.iloc[-1]['Blacklisted'])
        close['A'] = 100 * np.exp(.02)
        opening = close.copy()
        opening.iloc[-1, 0] = 200.
        daily, trades = backtest_pair_next_open(pair, close, opening, seed, 10000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        self.assertEqual(trades.iloc[-1]['Exit Reason'], 'End of window')
        self.assertAlmostEqual(trades.iloc[-1]['Exit z'], 2.)
        self.assertEqual(daily.iloc[-1]['Position'], 0)

if __name__ == '__main__':
    unittest.main()
