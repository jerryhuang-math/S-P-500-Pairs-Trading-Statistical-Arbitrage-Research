import warnings
from types import SimpleNamespace
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from rolling_kalman import rolling_signals, test_pair
from kalman_backtest import backtest_kalman_pair


class RollingTests(unittest.TestCase):
    def test_trailing_bounds_prefix_and_monthly_tests(self):
        rng = np.random.default_rng(42)
        x = 4 + np.cumsum(rng.normal(0, .01, 340))
        prices = pd.DataFrame({'A': np.exp(.2 + .9*x + rng.normal(0, .01, len(x))),
                               'B': np.exp(x)}, index=pd.bdate_range('2020-01-01', periods=len(x)))
        dates = prices.index[260:]
        windows = []
        def gate(history):
            windows.append(history.copy())
            return {'Passed': True}
        with patch('rolling_kalman.test_pair', side_effect=gate):
            full = rolling_signals(prices, dates, 1e-8, 1e-4)
        self.assertEqual(len(windows), len(set(dates.to_period('M'))))
        self.assertTrue(all(len(w) == 252 for w in windows))
        self.assertEqual(windows[0].index[-1], prices.index[259])
        with patch('rolling_kalman.test_pair', return_value={'Passed': True}):
            short = rolling_signals(prices.iloc[:300], dates[:40], 1e-8, 1e-4)
        pd.testing.assert_frame_equal(full.loc[short.index], short)
        changed = prices.copy()
        changed.iloc[:200] *= 2
        with patch('rolling_kalman.test_pair', return_value={'Passed': True}):
            trailing = rolling_signals(changed, dates, 1e-8, 1e-4)
        np.testing.assert_allclose(full[['Beta', 'z']], trailing[['Beta', 'z']])

    def test_failed_gate_exits_next_close_and_prevents_reentry(self):
        dates = pd.bdate_range('2022-01-01', periods=6)
        prices = pd.DataFrame({'A': 100., 'B': 100.}, index=dates)
        signals = pd.DataFrame({'z': 2., 'Beta': 1., 'Eligible': [True, True, False, False, False, False]}, index=dates)
        pair = dict(A='A', B='B', Beta=1., **{'Spread Mean': 0., 'Spread Std': 1.})
        daily, trades = backtest_kalman_pair(pair, prices.iloc[1:], signals, prices.iloc[0], 1000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades.iloc[0]['Exit Reason'], 'Cointegration failed')
        self.assertEqual(trades.iloc[0]['Exit Signal Date'], dates[2])
        self.assertEqual(trades.iloc[0]['Exit Date'], dates[3])
        self.assertTrue(daily.loc[dates[3]:, 'Position'].eq(0).all())

    def test_invalid_johansen_is_audited_without_warning(self):
        rng = np.random.default_rng(7)
        prices = pd.DataFrame(np.exp(rng.normal(4, .01, (100, 2))), columns=['A', 'B'])
        def complex_warning(*args, **kwargs):
            warnings.warn('Casting complex values to real', np.exceptions.ComplexWarning)
        invalid = SimpleNamespace(eig=np.array([np.nan, .1]), evec=np.eye(2), lr1=np.array([30., 1.]), cvt=np.ones((2, 3)))
        model = {'EG p-value': .001}
        for effect in [complex_warning, lambda *a, **k: invalid]:
            with patch('rolling_kalman.fit_direction', return_value=model), patch('rolling_kalman.coint_johansen', side_effect=effect):
                with warnings.catch_warnings(record=True) as caught:
                    result = test_pair(prices)
                self.assertEqual(len(caught), 0)
                self.assertFalse(result['Passed'])
                self.assertIn('Invalid cointegration fit', result['Status'])

    def test_real_valued_complex_eigensystem_is_accepted(self):
        rng = np.random.default_rng(9)
        prices = pd.DataFrame(np.exp(rng.normal(4, .01, (100, 2))), columns=['A', 'B'])
        roots = np.array([.3, .001], dtype=complex)
        trace = -98 * np.cumsum(np.log1p(-roots.real)[::-1])[::-1]
        result = SimpleNamespace(eig=roots, evec=np.eye(2, dtype=complex),
                                 rkt=np.zeros((98, 2)), lr1=trace, cvt=np.full((2, 3), 10.))
        def johansen(*args, **kwargs):
            warnings.warn('Casting complex values to real', np.exceptions.ComplexWarning)
            return result
        with patch('rolling_kalman.fit_direction', return_value={'EG p-value': .001}), patch('rolling_kalman.coint_johansen', side_effect=johansen):
            with warnings.catch_warnings(record=True) as caught:
                tested = test_pair(prices, correlation=-1.)
            self.assertEqual(len(caught), 0)
            self.assertTrue(tested['Passed'])
            result.eig[0] += .01j
            self.assertFalse(test_pair(prices, correlation=-1.)['Passed'])

    def test_cointegrated_pair_with_installed_numpy_and_statsmodels(self):
        rng = np.random.default_rng(42)
        x = 4 + np.cumsum(rng.normal(0, .01, 400))
        prices = pd.DataFrame({'A': np.exp(.2 + .9*x + rng.normal(0, .001, len(x))),
                               'B': np.exp(x)})
        with warnings.catch_warnings(record=True) as caught:
            result = test_pair(prices)
        self.assertEqual(len(caught), 0)
        self.assertTrue(result['Passed'], result)

    def test_missing_history_fails(self):
        prices = pd.DataFrame({'A': [np.nan]*252, 'B': [100.]*252})
        self.assertFalse(test_pair(prices)['Passed'])

if __name__ == '__main__':
    unittest.main()
