"""Causal two-state Kalman regression and next-close pair accounting."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from joint_grid_search import (decide_order, TRADE_COLUMNS, TRANSACTION_COST_BPS,
                               ENTRY_Z, EXIT_Z, STOP_Z)


def seed_state(logs, seed_sessions=60):
    """Initialize intercept and slope from the first historical observations."""
    if len(logs) <= seed_sessions or not np.isfinite(logs.to_numpy()).all():
        raise ValueError('Need complete history beyond the initial 60-session OLS seed')
    data = logs.iloc[:seed_sessions]
    x = np.column_stack([np.ones(len(data)), data.iloc[:, 1]])
    theta = np.linalg.lstsq(x, data.iloc[:, 0], rcond=None)[0]
    residual = data.iloc[:, 0].to_numpy() - x @ theta
    variance = max(float(residual @ residual / (len(data) - 2)), 1e-10)
    covariance = variance * np.linalg.pinv(x.T @ x) + np.eye(2) * 1e-12
    return theta, covariance


def kalman_trace(logs, q, r, seed_sessions=60):
    """Predict, score innovation, then update; no smoothing or future observations."""
    if not np.isfinite([q, r]).all() or q <= 0 or r <= 0:
        raise ValueError('Noise variances must be finite and positive')
    theta, covariance = seed_state(logs, seed_sessions)
    rows = []
    identity = np.eye(2)
    for date, values in logs.iloc[seed_sessions:].iterrows():
        y, x = values.iloc[0], values.iloc[1]
        h = np.array([1., x])
        prior_cov = covariance + q * identity
        error = float(y - h @ theta)
        variance = float(h @ prior_cov @ h + r)
        gain = prior_cov @ h / variance
        prior_alpha, prior_beta = theta
        theta = theta + gain * error
        # Joseph update keeps covariance positive semidefinite numerically.
        transform = identity - np.outer(gain, h)
        covariance = transform @ prior_cov @ transform.T + r * np.outer(gain, gain)
        rows.append({'Date': date, 'z': error / np.sqrt(variance), 'Innovation': error,
                     'Innovation variance': variance, 'Alpha': theta[0], 'Beta': theta[1],
                     'Prior Alpha': prior_alpha, 'Prior Beta': prior_beta})
    return pd.DataFrame(rows).set_index('Date')


def estimate_noise(histories, seed_sessions=60):
    """Estimate just two shared variances by pooled pre-trading innovation likelihood."""
    prepared = []
    for logs in histories:
        theta, covariance = seed_state(logs, seed_sessions)
        prepared.append((logs.iloc[seed_sessions:].to_numpy(), theta, covariance))
    if not prepared:
        raise ValueError('No pairs available for noise estimation')
    def objective(log_variances):
        q, r = np.exp(log_variances)
        total = 0.
        # Scalar covariance recursion avoids allocating dataframes during optimization.
        for values, initial_theta, initial_cov in prepared:
            a, b = initial_theta
            p00, p01, p11 = initial_cov[0, 0], initial_cov[0, 1], initial_cov[1, 1]
            for y, x in values:
                p00 += q
                p11 += q
                v0, v1 = p00 + x * p01, p01 + x * p11
                variance = v0 + x * v1 + r
                error = y - a - b * x
                total += .5 * (np.log(2 * np.pi * variance) + error * error / variance)
                a += v0 * error / variance
                b += v1 * error / variance
                p00 -= v0 * v0 / variance
                p01 -= v0 * v1 / variance
                p11 -= v1 * v1 / variance
        return float(total)
    bounds = [(np.log(1e-12), np.log(1e-3)), (np.log(1e-10), np.log(.1))]
    starts = [np.log([1e-8, 1e-4]), np.log([1e-6, 1e-3])]
    results = [minimize(objective, start, method='L-BFGS-B', bounds=bounds) for start in starts]
    valid = [result for result in results if result.success and np.isfinite(result.fun)]
    if not valid:
        raise RuntimeError('Noise estimation failed: ' + '; '.join(str(x.message) for x in results))
    best = min(valid, key=lambda result: result.fun)
    q, r = np.exp(best.x)
    boundary = any(np.isclose(best.x[i], edge, atol=1e-3) for i, bound in enumerate(bounds) for edge in bound)
    return float(q), float(r), {'negative_log_likelihood': float(best.fun),
                              'success': bool(best.success), 'at_bound': bool(boundary),
                              'log_variance_bounds': bounds}


def backtest_kalman_pair(pair, trading, signals, formation_last, initial_capital,
                  cost_bps=None, *, entry_z=None, exit_z=None, stop_z=None):
    """Use causal filter signals; next-close fills and fixed units until exit."""
    if cost_bps is None:
        cost_bps = TRANSACTION_COST_BPS
    entry_z = ENTRY_Z if entry_z is None else entry_z
    exit_z = EXIT_Z if exit_z is None else exit_z
    stop_z = STOP_Z if stop_z is None else stop_z
    if not np.isfinite([entry_z, exit_z, stop_z]).all() or not 0 <= exit_z < entry_z < stop_z:
        raise ValueError("Require finite thresholds with 0 <= exit_z < entry_z < stop_z")
    a, b = pair["A"], pair["B"]
    beta, mean, std = (float(pair[key]) for key in ["Beta", "Spread Mean", "Spread Std"])
    if initial_capital <= 0 or cost_bps < 0 or std <= 0:
        raise ValueError("Invalid capital, cost, or spread scale")
    data = trading[[a, b]]
    if data.empty or not (np.isfinite(data) & data.gt(0)).all().all():
        raise ValueError(f"{a}/{b}: incomplete or invalid trading prices")
    z = signals['z'].reindex(data.index)
    if not np.isfinite(z).all():
        raise ValueError('Missing or nonfinite Kalman signals')
    previous_z = float(signals.loc[formation_last.name, 'z'])
    previous_beta = float(signals.loc[formation_last.name, 'Beta'])
    previous_date = formation_last.name
    pending, blacklisted = decide_order(0, previous_z, False, entry_z, exit_z, stop_z)
    def gated_order(direction, z_value, blocked, date):
        action, blocked = decide_order(direction, z_value, blocked, entry_z, exit_z, stop_z)
        if 'Eligible' in signals and not bool(signals.loc[date, 'Eligible']):
            action = (0, 'Cointegration failed') if direction else None
        return action, blocked

    pending, blacklisted = gated_order(0, previous_z, False, previous_date)
    cash = equity = initial_capital
    units = np.zeros(2)
    direction, active_trade = 0, None
    rows, trades = [], []
    rate = cost_bps / 10_000

    for i, (date, prices) in enumerate(data.iterrows()):
        px = prices.to_numpy(dtype=float)
        prior_equity = equity
        before_trade = cash + units @ px
        if before_trade <= 0:
            raise ValueError(f"{a}/{b}: capital exhausted on {date}")
        cost, traded_value, reason = 0.0, 0.0, ""
        action = pending
        final_close = i == len(data) - 1
        if final_close:
            action = (0, "End of window") if direction else None
        if action is not None:
            target, reason = action
            if target == 0 and direction:
                traded_value = float(np.abs(units * px).sum())
                cost = rate * traded_value
                cash += float(units @ px) - cost
                units = np.zeros(2)
                active_trade.update({
                    "Exit Signal Date": pd.NaT if final_close else previous_date,
                    "Exit Date": date,
                    "Exit Signal z": np.nan if final_close else previous_z,
                    "Exit z": z.loc[date], "Exit Reason": reason,
                    "Net P/L ($)": cash - active_trade["Entry Equity ($)"],
                    "Costs ($)": active_trade["Entry Cost ($)"] + cost,
                })
                active_trade["Net Return"] = (active_trade["Net P/L ($)"]
                                               / active_trade["Entry Equity ($)"])
                trades.append(active_trade)
                active_trade, direction = None, 0
            elif target and direction == 0:
                weights = target * np.array([1.0, -previous_beta]) / (1 + abs(previous_beta))
                units = before_trade / (1 + rate) * weights / px
                traded_value = float(np.abs(units * px).sum())
                cost = rate * traded_value
                cash -= float(units @ px) + cost
                direction = target
                active_trade = {
                    "A": a, "B": b, "Entry Signal Date": previous_date,
                    "Entry Date": date, "Direction": direction,
                    "Entry Signal z": previous_z, "Entry z": z.loc[date],
                    "Entry Beta": previous_beta,
                    "Entry Equity ($)": before_trade, "Entry Cost ($)": cost,
                }
        equity = float(cash + units @ px)
        if equity <= 0:
            raise ValueError(f"{a}/{b}: capital exhausted after costs on {date}")
        pending = None
        if not final_close:
            pending, blacklisted = gated_order(direction, float(z.loc[date]), blacklisted, date)
        rows.append({
            "Date": date, "z": z.loc[date], "Position": direction,
            "Blacklisted": blacklisted, "Equity": equity,
            "Net Return": equity / prior_equity - 1,
            "Before Trade Equity": before_trade,
            "Costs ($)": cost, "Traded Value ($)": traded_value,
            "Turnover": traded_value / before_trade, "Action": reason,
            "Units A": units[0], "Units B": units[1],
        })
        previous_date, previous_z = date, float(z.loc[date])
        previous_beta = float(signals.loc[date, "Beta"])
    daily = pd.DataFrame(rows).set_index("Date")
    daily["Gross Equity"] = daily["Equity"] + daily["Costs ($)"].cumsum()
    return daily, pd.DataFrame(trades, columns=[*TRADE_COLUMNS, "Entry Beta"])



def continuous_signals(formation, trading, q, r):
    """Initialize once on formation; carry the posterior through all trading bars.

    The last formation close supplies the first possible entry signal, as in the
    constant-coefficient baseline. Trading innovations are scored before update,
    using the fixed formation residual scale to isolate coefficient adaptation.
    """
    if formation.empty or trading.empty or formation.index.max() >= trading.index.min():
        raise ValueError('Need nonempty formation strictly preceding trading')
    if not formation.columns.equals(trading.columns):
        raise ValueError('Formation and trading pair direction must match')
    prices = pd.concat([formation, trading])
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError('Prices must have unique increasing dates')
    if not (np.isfinite(prices) & prices.gt(0)).all().all():
        raise ValueError('Need complete positive formation and trading prices')
    logs = np.log(prices)
    n = len(formation)
    theta, _ = seed_state(logs, seed_sessions=n)
    residual = logs.iloc[:n, 0].to_numpy() - np.column_stack([np.ones(n), logs.iloc[:n, 1]]) @ theta
    scale = float(np.std(residual, ddof=1))
    if not np.isfinite(scale) or scale <= 1e-12:
        raise ValueError('Degenerate formation residual scale')
    trace = kalman_trace(logs, q, r, seed_sessions=n)
    trace['z'] = trace['Innovation'] / scale
    seed = pd.DataFrame({'z': [residual[-1] / scale], 'Alpha': [theta[0]],
                         'Beta': [theta[1]], 'Prior Alpha': [theta[0]],
                         'Prior Beta': [theta[1]], 'Innovation': [residual[-1]],
                         'Innovation variance': [np.nan]}, index=formation.index[-1:])
    signal = pd.concat([seed, trace])
    signal['Formation Fit End'] = formation.index[-1]
    signal['Spread Std'] = scale
    signal.index.name = 'Date'
    return signal
