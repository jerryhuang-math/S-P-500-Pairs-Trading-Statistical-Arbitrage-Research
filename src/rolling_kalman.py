"""Rolling structural screening and strictly trailing Kalman signals."""
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from joint_grid_search import fit_direction
from kalman_backtest import kalman_trace


def test_pair(prices, correlation=.8, significance=.01):
    """Both tests use the same observations and fixed column direction."""
    if significance != .01:
        raise ValueError('Johansen critical column is configured for 1%')
    if len(prices) < 60 or not (np.isfinite(prices) & prices.gt(0)).all().all():
        return {'Passed': False, 'Status': 'Incomplete history'}
    logs = np.log(prices)
    corr = logs.diff().iloc[1:].corr().iloc[0, 1]
    try:
        model = fit_direction(logs, *prices.columns)
        with warnings.catch_warnings(record=True):
            # NumPy 2.5 eig returns complex dtype even for real roots.
            # Validate the roots and vectors below before accepting statistics.
            warnings.simplefilter('error', RuntimeWarning)
            warnings.simplefilter('always', np.exceptions.ComplexWarning)
            joh = coint_johansen(logs.to_numpy(), det_order=0, k_ar_diff=1)
        if joh is None:
            raise ValueError('Missing Johansen result')
        for values in (joh.eig, joh.evec):
            real_values = np.real_if_close(values)
            if np.iscomplexobj(real_values) or not np.isfinite(real_values).all():
                raise ValueError('Complex or nonfinite Johansen eigensystem')
        eigenvalues = np.real_if_close(joh.eig)
        for values in (joh.lr1, joh.cvt):
            if np.iscomplexobj(values) or not np.isfinite(values).all():
                raise ValueError('Complex or nonfinite Johansen result')
        if np.any(eigenvalues < 0) or np.any(eigenvalues >= 1):
            raise ValueError('Johansen eigenvalues outside [0, 1)')
        expected_trace = -len(joh.rkt) * np.cumsum(np.log1p(-eigenvalues)[::-1])[::-1]
        if not np.allclose(joh.lr1, expected_trace, rtol=1e-10, atol=1e-10):
            raise ValueError('Inconsistent Johansen trace statistics')
        # Exactly rank one: reject rank zero, do not reject rank <= one.
        jp = bool(joh.lr1[0] > joh.cvt[0, 2] and joh.lr1[1] <= joh.cvt[1, 2])
        ep = model['EG p-value'] < significance
        return {**model, 'Correlation': corr, 'EG Passed': ep,
                'Johansen Passed': jp, 'Johansen Trace': float(joh.lr1[0]),
                'Passed': bool(corr > correlation and ep and jp)}
    except (ValueError, np.linalg.LinAlgError, Warning) as exc:
        return {'Passed': False, 'Johansen Passed': False,
                'Status': f'Invalid cointegration fit: {type(exc).__name__}: {exc}'}


def rolling_signals(prices, signal_dates, q, r, lookback=60, coint_sessions=252):
    """Monthly trailing tests; daily filters refitted on exactly lookback past bars.

    Today's innovation is scored before today's update; its posterior beta can
    size an order at the following close. No filter state survives the lookback.
    """
    rows, last_month, gate = [], None, None
    for date in signal_dates:
        pos = prices.index.get_loc(date)
        if pos < max(lookback, coint_sessions):
            raise ValueError('Insufficient trailing observations')
        month = (date.year, date.month)
        if month != last_month:
            history = prices.iloc[pos-coint_sessions:pos]
            gate = test_pair(history)
            test_end = history.index[-1]
            last_month = month
        logs = np.log(prices.iloc[pos-lookback:pos+1])
        row = kalman_trace(logs, q, r, seed_sessions=lookback-1).iloc[-1].to_dict()
        row.update({'Date': date, 'Eligible': gate['Passed'],
                    'Cointegration Fit End': test_end,
                    'Cointegration Status': gate.get('Status', 'OK'),
                    'Kalman Fit Start': logs.index[0],
                    'Kalman Fit End': prices.index[pos-1]})
        rows.append(row)
    return pd.DataFrame(rows).set_index('Date')
