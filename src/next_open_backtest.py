"""Next-open execution experiment, sharing the baseline's signal and account rules.

Prices are synthetic adjusted units. Final-window liquidation remains at the
scheduled last close; other orders fill at the next session's adjusted open.
"""
import numpy as np
import pandas as pd
from joint_grid_search import (decide_order, TRADE_COLUMNS, TRANSACTION_COST_BPS,
                               ENTRY_Z, EXIT_Z, STOP_Z)


def adjusted_open(frame):
    """Apply the vendor's daily close adjustment factor to raw open prices."""
    values = frame[['Open', 'Close', 'Adj Close']].apply(pd.to_numeric, errors='coerce')
    if not (np.isfinite(values) & values.gt(0)).all().all():
        raise ValueError('Missing, nonfinite, or nonpositive Open / Close / Adj Close')
    return (values['Open'] * (values['Adj Close'] / values['Close'])).rename('Adj Open')


def backtest_pair_next_open(pair, trading, opening, formation_last, initial_capital,
                  cost_bps=None, *, entry_z=None, exit_z=None, stop_z=None):
    """Prior-close signals, next-open fills, close marks; final liquidation at close."""
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
    opens = opening.reindex(index=data.index, columns=[a, b])
    if not (np.isfinite(opens) & opens.gt(0)).all().all():
        raise ValueError(f"{a}/{b}: incomplete or invalid opening prices")
    z = (np.log(data[a]) - beta * np.log(data[b]) - mean) / std
    previous_z = float((np.log(formation_last[a]) - beta * np.log(formation_last[b]) - mean) / std)
    previous_date = formation_last.name
    pending, blacklisted = decide_order(0, previous_z, False, entry_z, exit_z, stop_z)
    cash = equity = initial_capital
    units = np.zeros(2)
    direction, active_trade = 0, None
    rows, trades = [], []
    rate = cost_bps / 10_000

    for i, (date, prices) in enumerate(data.iterrows()):
        close_px = prices.to_numpy(dtype=float)
        # The final session keeps the baseline's scheduled close liquidation.
        px = (close_px if i == len(data) - 1 else opens.loc[date].to_numpy(dtype=float))
        fill_z = float((np.log(px[0]) - beta * np.log(px[1]) - mean) / std)
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
                    "Exit z": fill_z, "Exit Reason": reason,
                    "Net P/L ($)": cash - active_trade["Entry Equity ($)"],
                    "Costs ($)": active_trade["Entry Cost ($)"] + cost,
                })
                active_trade["Net Return"] = (active_trade["Net P/L ($)"]
                                               / active_trade["Entry Equity ($)"])
                trades.append(active_trade)
                active_trade, direction = None, 0
            elif target and direction == 0:
                weights = target * np.array([1.0, -beta]) / (1 + abs(beta))
                units = before_trade / (1 + rate) * weights / px
                traded_value = float(np.abs(units * px).sum())
                cost = rate * traded_value
                cash -= float(units @ px) + cost
                direction = target
                active_trade = {
                    "A": a, "B": b, "Entry Signal Date": previous_date,
                    "Entry Date": date, "Direction": direction,
                    "Entry Signal z": previous_z, "Entry z": fill_z,
                    "Entry Equity ($)": before_trade, "Entry Cost ($)": cost,
                }
        equity = float(cash + units @ close_px)
        if equity <= 0:
            raise ValueError(f"{a}/{b}: capital exhausted after costs on {date}")
        pending = None
        if not final_close:
            pending, blacklisted = decide_order(direction, float(z.loc[date]), blacklisted,
                                               entry_z, exit_z, stop_z)
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
    daily = pd.DataFrame(rows).set_index("Date")
    daily["Gross Equity"] = daily["Equity"] + daily["Costs ($)"].cumsum()
    return daily, pd.DataFrame(trades, columns=TRADE_COLUMNS)

