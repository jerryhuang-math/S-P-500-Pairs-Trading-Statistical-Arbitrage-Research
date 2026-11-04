import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from kalman_backtest import kalman_trace, estimate_noise, backtest_kalman_pair
from joint_grid_search import backtest_pair


class KalmanTests(unittest.TestCase):
    def history(self):
        rng = np.random.default_rng(12)
        x = 4 + np.cumsum(rng.normal(0, .01, 120))
        y = .2 + .9 * x + rng.normal(0, .01, len(x))
        return pd.DataFrame({'A': y, 'B': x}, index=pd.bdate_range('2020-01-01', periods=len(x)))

    def test_prefix_invariance_and_prediction_before_update(self):
        logs = self.history()
        full = kalman_trace(logs, 1e-8, 1e-4)
        short = kalman_trace(logs.iloc[:90], 1e-8, 1e-4)
        pd.testing.assert_frame_equal(full.loc[short.index], short)
        error = logs.A.reindex(full.index) - full['Prior Alpha'] - full['Prior Beta'] * logs.B.reindex(full.index)
        np.testing.assert_allclose(full.Innovation, error, atol=1e-12)
        self.assertTrue(np.isfinite(full.to_numpy()).all())
        self.assertTrue(full['Innovation variance'].gt(0).all())

    def test_noise_estimation_is_finite(self):
        q, r, info = estimate_noise([self.history()])
        self.assertGreater(q, 0)
        self.assertGreater(r, 0)
        self.assertTrue(info['success'])

    def test_frozen_signals_reproduce_baseline_accounting(self):
        dates = pd.bdate_range('2020-01-02', periods=8)
        z = np.array([2., .2, 0., -2., -5., 0., 2., 2.])
        close = pd.DataFrame({'A': 100 * np.exp(z * .01), 'B': 100.}, index=dates)
        pair = {'A': 'A', 'B': 'B', 'Beta': 1., 'Spread Mean': 0., 'Spread Std': .01}
        seed = pd.Series({'A': 100., 'B': 100.}, name=dates[0] - pd.Timedelta(days=1))
        signals = pd.DataFrame({'z': np.r_[0., z], 'Beta': 1.}, index=pd.DatetimeIndex([seed.name, *dates]))
        expected_daily, expected_trades = backtest_pair(pair, close, seed, 10000., 5., entry_z=1.5, exit_z=.5, stop_z=4.)
        daily, trades = backtest_kalman_pair(pair, close, signals, seed, 10000., 5., entry_z=1.5, exit_z=.5, stop_z=4.)
        pd.testing.assert_frame_equal(daily, expected_daily)
        pd.testing.assert_frame_equal(trades.drop(columns='Entry Beta'), expected_trades)
        np.testing.assert_allclose(daily.Equity.iloc[-1] - 10000., trades['Net P/L ($)'].sum())
        signals.loc[dates[1]:, 'Beta'] = 3.
        _, changed = backtest_kalman_pair(pair, close, signals, seed, 10000., 0., entry_z=1.5, exit_z=.5, stop_z=4.)
        self.assertEqual(changed.iloc[0]['Entry Beta'], 1.)

if __name__ == '__main__':
    unittest.main()


class ContinuousSignalTests(KalmanTests):
    def test_full_formation_seed_and_continuous_causal_state(self):
        from kalman_backtest import continuous_signals, seed_state
        logs = self.history()
        formation, trading = np.exp(logs.iloc[:80]), np.exp(logs.iloc[80:])
        signals = continuous_signals(formation, trading, 1e-8, 1e-4)
        theta, _ = seed_state(logs, seed_sessions=80)
        np.testing.assert_allclose(signals.iloc[0][['Alpha', 'Beta']].to_numpy(dtype=float), theta)
        np.testing.assert_allclose(signals['Prior Alpha'].iloc[1:], signals['Alpha'].iloc[:-1])
        np.testing.assert_allclose(signals['Prior Beta'].iloc[1:], signals['Beta'].iloc[:-1])
        shortened = continuous_signals(formation, trading.iloc[:15], 1e-8, 1e-4)
        pd.testing.assert_frame_equal(signals.loc[shortened.index], shortened)
        changed = trading.copy()
        changed.iloc[-1, 0] *= 1.1
        altered = continuous_signals(formation, changed, 1e-8, 1e-4)
        pd.testing.assert_frame_equal(signals.iloc[:-1], altered.iloc[:-1])
        self.assertAlmostEqual(signals.iloc[-1]['Prior Beta'], altered.iloc[-1]['Prior Beta'])
        self.assertNotEqual(signals.iloc[-1]['Beta'], altered.iloc[-1]['Beta'])
        np.testing.assert_allclose(signals['z'], signals['Innovation'] / signals['Spread Std'])
