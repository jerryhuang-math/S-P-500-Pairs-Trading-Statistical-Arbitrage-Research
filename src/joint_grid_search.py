"""Joint grid search using the established notebook's account and execution rules.

Formation caches contain only training data. Unit-capital simulations can be
scaled exactly because holdings and proportional costs are linear in capital.
"""
import csv
import hashlib
import json
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from inspect import signature
from itertools import combinations, product
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import statsmodels.api as sm
from risk_free import annualized_treasury_return, load_treasury_yields
from statsmodels.tsa.stattools import adfuller, coint

DATA_START = pd.Timestamp("2015-01-01")
DATA_END_EXCLUSIVE = pd.Timestamp("2026-08-25")
HOLDOUT_START = DATA_END_EXCLUSIVE - pd.DateOffset(years=3)
COMMON_START = DATA_START + pd.DateOffset(months=18)
FORMATION_MONTHS, TRADING_MONTHS = 12, 2
CORRELATION_THRESHOLD, EG_SIGNIFICANCE = 0.8, 0.05
ENTRY_Z, EXIT_Z, STOP_Z = 1.5, 0.5, 3.0
TRANSACTION_COST_BPS, INITIAL_CAPITAL, TRADING_DAYS = 5.0, 100_000.0, 252
FORMATION_GRID = (3, 6, 12, 18)
TRADING_GRID = (2, 3, 6, 12)
CORRELATION_GRID, EG_GRID = (0.8, 0.9), (0.01, 0.05)
Z_GRID = tuple(product((1.5, 2.0, 2.5), (0.0, 0.5), (3.0, 3.5, 4.0, 4.5)))
PARAMETER_NAMES = ("formation_months", "trading_months", "correlation_threshold",
                   "eg_significance", "entry_z", "exit_z", "stop_z")


def read_training_series(path, start=DATA_START, end=HOLDOUT_START):
    """Date-gate mixed CSV rows before interpreting adjusted prices."""
    if not DATA_START <= start < end <= HOLDOUT_START:
        raise ValueError("Price loading must stay inside the training partition")
    observations = {}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"Date", "Adj Close"}.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing Date / Adj Close columns: {path.name}")
        for row in reader:
            date = pd.Timestamp(row["Date"])
            if pd.isna(date):
                raise ValueError(f"Missing date: {path.name}")
            if not start <= date < end:
                continue
            if date in observations:
                raise ValueError(f"Duplicate training date: {path.name}, {date}")
            value = pd.to_numeric(row["Adj Close"], errors="coerce")
            observations[date] = float(value)
    return pd.Series(observations, dtype=float, name=path.stem).sort_index()


def make_windows(start, end, formation_months=None, trading_months=None,
                 step_months=None, first_trading_start=None):
    formation_months = FORMATION_MONTHS if formation_months is None else formation_months
    trading_months = TRADING_MONTHS if trading_months is None else trading_months
    step_months = trading_months if step_months is None else step_months
    if any(not isinstance(value, (int, np.integer)) or value <= 0
           for value in (formation_months, trading_months, step_months)):
        raise ValueError("Window lengths must be positive integer calendar months")
    if step_months != trading_months:
        raise ValueError("This independent-account engine requires contiguous, nonoverlapping trading windows")
    earliest_start = start + pd.DateOffset(months=formation_months)
    trade_start = earliest_start if first_trading_start is None else pd.Timestamp(first_trading_start)
    if not earliest_start <= trade_start < end:
        raise ValueError("First trading date must allow full formation history and precede the end")
    rows = []
    while trade_start < end:
        scheduled_end = trade_start + pd.DateOffset(months=trading_months)
        trade_end = min(scheduled_end, end)
        rows.append({
            "Window": len(rows) + 1,
            "Formation Start": trade_start - pd.DateOffset(months=formation_months),
            "Formation End Exclusive": trade_start,
            "Trading Start": trade_start,
            "Trading End Exclusive": trade_end,
            "Shortened": trade_end < scheduled_end,
        })
        trade_start = trade_start + pd.DateOffset(months=step_months)
    return pd.DataFrame(rows)


def interval(data, start, end):
    return data.loc[(data.index >= start) & (data.index < end)]


def screen_correlations(formation, mapping, correlation_threshold=0.8):
    valid = np.isfinite(formation) & formation.gt(0)
    eligibility = pd.DataFrame({
        "Valid Sessions": valid.sum(),
        "Required Sessions": len(formation),
        "Complete Positive History": valid.all(),
        "Nonconstant": formation.nunique() > 1,
    })
    eligibility["Eligible"] = (eligibility["Complete Positive History"]
                                & eligibility["Nonconstant"])
    eligibility.index.name = "Ticker"
    eligible = eligibility.index[eligibility["Eligible"]]
    log_returns = np.log(formation.loc[:, eligible]).diff().iloc[1:]
    rows = []
    for group_code, group in mapping.groupby("Industry Group Code", sort=True):
        tickers = sorted(group["Ticker"])
        eligible_tickers = [ticker for ticker in tickers if ticker in eligible]
        correlations = log_returns[eligible_tickers].corr()
        for a, b in combinations(tickers, 2):
            ready = a in eligible and b in eligible
            corr = correlations.loc[a, b] if ready else np.nan
            rows.append({
                "Industry Group Code": group_code,
                "Industry Group": group["Industry Group"].iloc[0],
                "Ticker 1": a, "Ticker 2": b,
                "Return Observations": len(log_returns) if ready else 0,
                "Correlation": corr,
                "Screen Passed": bool(np.isfinite(corr) and corr > correlation_threshold),
                "Status": ("OK" if np.isfinite(corr) else "Undefined correlation")
                          if ready else "Incomplete or constant formation history",
            })
    columns = ["Industry Group Code", "Industry Group", "Ticker 1", "Ticker 2",
               "Return Observations", "Correlation", "Screen Passed", "Status"]
    return pd.DataFrame(rows, columns=columns), eligibility.reset_index()


def fit_direction(log_prices, a, b):
    """Estimate OLS and a calibrated EG test on the identical formation sample."""
    fit = sm.OLS(log_prices[a], sm.add_constant(log_prices[[b]], has_constant="add")).fit()
    alpha, beta = float(fit.params["const"]), float(fit.params[b])
    spread = log_prices[a] - beta * log_prices[b]
    mean, std = float(spread.mean()), float(spread.std(ddof=1))
    if not np.isfinite([alpha, beta, mean, std]).all() or std <= 1e-12:
        raise ValueError("Degenerate spread or nonfinite model")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        statistic, pvalue, critical = coint(
            log_prices[a], log_prices[b], trend="c", method="aeg",
            maxlag=None, autolag="aic", return_results=False,
        )
    # Retain lag diagnostics only; ordinary ADF p-values/critical values are not used.
    adf_options = {"result_object": False} if "result_object" in signature(adfuller).parameters else {}
    adf = adfuller(fit.resid, regression="n", maxlag=None, autolag="AIC", **adf_options)
    if not np.isfinite([statistic, pvalue, critical[1]]).all():
        raise ValueError("Nonfinite EG result")
    np.testing.assert_allclose(statistic, adf[0], rtol=1e-8, atol=1e-8)
    return {
        "Alpha": alpha, "Beta": beta, "Spread Mean": mean, "Spread Std": std,
        "EG Statistic": statistic, "EG p-value": pvalue,
        "EG 1% Critical Value": critical[0], "EG 5% Critical Value": critical[1], "ADF Lags": adf[2],
        "ADF Observations": adf[3], "EG Passed": bool(statistic < critical[1]),
        "Status": "OK",
    }


def decide_order(direction, z, blacklisted, entry_z=None, exit_z=None, stop_z=None):
    """Return the next-close target and the persistent blacklist state."""
    entry_z = ENTRY_Z if entry_z is None else entry_z
    exit_z = EXIT_Z if exit_z is None else exit_z
    stop_z = STOP_Z if stop_z is None else stop_z
    if direction:
        if direction * z <= -stop_z:
            return (0, "Stop loss"), True
        if direction * z >= -exit_z:
            return (0, "Mean reversion"), blacklisted
    elif not blacklisted and entry_z <= abs(z) < stop_z:
        return (-1 if z > 0 else 1, "Entry"), blacklisted
    return None, blacklisted


TRADE_COLUMNS = ["A", "B", "Entry Signal Date", "Entry Date", "Direction",
                 "Entry Signal z", "Entry z", "Entry Equity ($)", "Entry Cost ($)",
                 "Exit Signal Date", "Exit Date", "Exit Signal z", "Exit z",
                 "Exit Reason", "Net P/L ($)", "Net Return", "Costs ($)"]


def backtest_pair(pair, trading, formation_last, initial_capital,
                  cost_bps=None, *, entry_z=None, exit_z=None, stop_z=None):
    """Run one frozen model with lagged signals, fixed holdings, and a blacklist."""
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
                weights = target * np.array([1.0, -beta]) / (1 + abs(beta))
                units = before_trade / (1 + rate) * weights / px
                traded_value = float(np.abs(units * px).sum())
                cost = rate * traded_value
                cash -= float(units @ px) + cost
                direction = target
                active_trade = {
                    "A": a, "B": b, "Entry Signal Date": previous_date,
                    "Entry Date": date, "Direction": direction,
                    "Entry Signal z": previous_z, "Entry z": z.loc[date],
                    "Entry Equity ($)": before_trade, "Entry Cost ($)": cost,
                }
        equity = float(cash + units @ px)
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


def combine_accounts(accounts, dates, initial_capital):
    columns = ["Equity", "Before Trade Equity", "Costs ($)", "Traded Value ($)"]
    if accounts:
        daily = sum((account[columns] for account in accounts))
        daily["Active Pairs"] = sum((account["Position"].ne(0).astype(int) for account in accounts))
        daily["Blacklisted Pairs"] = sum((account["Blacklisted"].astype(int) for account in accounts))
    else:
        daily = pd.DataFrame(0.0, index=dates, columns=columns)
        daily[["Equity", "Before Trade Equity"]] = initial_capital
        daily[["Active Pairs", "Blacklisted Pairs"]] = 0
    previous = daily["Equity"].shift(1, fill_value=initial_capital)
    daily["Net Return"] = daily["Equity"] / previous - 1
    daily["Turnover"] = daily["Traded Value ($)"] / daily["Before Trade Equity"]
    daily["Gross Equity"] = daily["Equity"] + daily["Costs ($)"].cumsum()
    daily.index.name = "Date"
    return daily


def performance_metrics(daily, trades, initial_capital, treasury_yields=None):
    returns = daily["Net Return"]
    volatility = returns.std(ddof=1)
    cumulative = daily["Equity"].iloc[-1] / initial_capital - 1
    peak = daily["Equity"].cummax().clip(lower=initial_capital)
    annualized_return = (1 + cumulative) ** (TRADING_DAYS / len(daily)) - 1
    annualized_volatility = volatility * np.sqrt(TRADING_DAYS)
    risk_free_rate = annualized_treasury_return(daily.index, treasury_yields, TRADING_DAYS)
    return {
        "Cumulative Return": cumulative,
        "Gross Cumulative Return": daily["Gross Equity"].iloc[-1] / initial_capital - 1,
        "Annualized Return": annualized_return,
        "Annualized Volatility": annualized_volatility,
        "Annualized Risk-Free Return": risk_free_rate,
        "Sharpe Ratio": (annualized_return - risk_free_rate) / annualized_volatility
                        if volatility > 0 else np.nan,
        "Maximum Drawdown": float(-(daily["Equity"] / peak - 1).min()),
        "Number of Trades": len(trades),
        "Win Rate": trades["Net P/L ($)"].gt(0).mean() if len(trades) else np.nan,
        "Average P/L per Trade ($)": trades["Net P/L ($)"].mean(),
        "Average Return per Trade": trades["Net Return"].mean(),
        "Turnover (x)": daily["Turnover"].sum(),
        "Transaction Costs ($)": daily["Costs ($)"].sum(),
        "Costs / Initial Capital": daily["Costs ($)"].sum() / initial_capital,
    }



def parameter_grid():
    return [dict(zip(PARAMETER_NAMES, values))
            for values in product(FORMATION_GRID, TRADING_GRID, CORRELATION_GRID,
                                  EG_GRID, (1.5, 2.0, 2.5), (0.0, 0.5),
                                  (3.0, 3.5, 4.0, 4.5)) if values[1] <= values[0]]


def parameter_id(p):
    return '_'.join(f'{key}_{p[key]:g}' for key in PARAMETER_NAMES)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, default=str, allow_nan=False))
    temporary.replace(path)


def atomic_csv(frame, path, **kwargs):
    temporary = path.with_suffix(path.suffix + '.tmp')
    frame.to_csv(temporary, **kwargs)
    temporary.replace(path)


class GridSearch:
    def __init__(self, project, output=None, cost_bps=5.0, initial_capital=100_000.0):
        import threading
        from importlib.metadata import version
        self.project = Path(project).resolve()
        self.output = Path(output or self.project / 'outputs' / 'joint_grid_search')
        if not np.isfinite([cost_bps, initial_capital]).all() or cost_bps < 0 or initial_capital <= 0:
            raise ValueError('Invalid costs or initial capital')
        self.cost_bps, self.initial_capital = float(cost_bps), float(initial_capital)
        self.filtered = self.project / 'data' / 'Filter_historical'
        self.raw = self.project / 'data' / 'historical'
        self.mapping_file = self.project / 'data' / 'gics' / 'ticker_gics.csv'
        # Content fingerprints prevent stale results after data, engine, or environment changes.
        digest = hashlib.sha256(Path(__file__).read_bytes())
        digest.update(Path(__file__).with_name("risk_free.py").read_bytes())
        self.treasury_yields = load_treasury_yields(
            self.project / "data" / "risk_free" / "DGS3MO.csv")
        annualized_treasury_return(
            mcal.get_calendar("NYSE").valid_days(COMMON_START, HOLDOUT_START - pd.Timedelta(days=1)).tz_localize(None),
            self.treasury_yields)
        digest.update(self.treasury_yields.to_csv().encode())
        self.versions = {name: version(name) for name in
                         ['numpy', 'pandas', 'statsmodels', 'pandas_market_calendars']}
        digest.update(json.dumps(self.versions, sort_keys=True).encode())
        digest.update(f'{cost_bps}:{initial_capital}'.encode())
        paths = [self.mapping_file, *sorted(self.filtered.glob('*.csv')),
                 *sorted(self.raw.glob('*.csv'))]
        if len(paths) == 1:
            raise FileNotFoundError('No input price files found')
        for path in paths:
            digest.update(str(path.relative_to(self.project)).encode())
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
        self.run_id = digest.hexdigest()[:20]
        self.folder = self.output / self.run_id
        self.cache_folder = self.folder / 'formation_cache'
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._formation_locks = {}
        self._raw_cache = {}
        self.prices = None
        write_json(self.folder / 'search_manifest.json', {
            'run_id': self.run_id, 'parameters': parameter_grid(),
            'sharpe': '(annualized strategy return - annualized Treasury benchmark return) / annualized volatility',
            'risk_free_source': 'FRED DGS3MO; lagged investment-basis yields, effective daily accrual, 252 sessions/year',
            'data_start': DATA_START, 'common_trading_start': COMMON_START,
            'end_exclusive': HOLDOUT_START, 'holdout_start': HOLDOUT_START,
            'cost_bps_per_leg': self.cost_bps, 'initial_capital': self.initial_capital,
            'versions': self.versions, 'formation_correlation': 'daily log returns; strict >',
            'eg_rule': 'statistic below returned 1% or 5% EG critical value',
            'direction_choice': 'lowest EG p-value among passing directions',
            'final_window': 'shorten to common evaluation end; liquidate at final close',
            'execution': 'next close; frozen models; stop blacklists pair until next window',
        })

    def load_data(self):
        sessions = mcal.get_calendar('NYSE').valid_days(
            DATA_START, HOLDOUT_START - pd.Timedelta(days=1)).tz_localize(None)
        self.prices = pd.concat([read_training_series(p)
                                 for p in sorted(self.filtered.glob('*.csv'))], axis=1).reindex(sessions)
        self.prices.index.name = 'Date'
        self.mapping = pd.read_csv(self.mapping_file, dtype='string')
        self.mapping['Ticker'] = self.mapping['Ticker'].str.strip().str.upper()
        self.mapping['Industry Group Code'] = self.mapping['Industry Group Code'].str.strip()
        if self.mapping['Ticker'].duplicated().any():
            raise ValueError('Duplicate tickers in GICS mapping')
        valid = self.mapping['Industry Group Code'].str.fullmatch(r'\d{4}', na=False)
        self.mapping = self.mapping.loc[valid & self.mapping['Ticker'].isin(self.prices.columns)].copy()
        return self

    def schedule(self, formation_months, trading_months):
        return make_windows(DATA_START, HOLDOUT_START, formation_months, trading_months,
                            trading_months, COMMON_START)

    def formation(self, window):
        start, end = window['Formation Start'], window['Formation End Exclusive']
        key = f'{start:%Y%m%d}_{end:%Y%m%d}'
        with self._lock:
            lock = self._formation_locks.setdefault(key, __import__('threading').Lock())
        with lock:
            path = self.cache_folder / f'{key}.pkl'
            if path.exists():
                # Only load caches generated locally by this engine in the fingerprinted run folder.
                return pd.read_pickle(path)
            formation = interval(self.prices, start, end)
            comparisons, eligibility = screen_correlations(formation, self.mapping, min(CORRELATION_GRID))
            rows = []
            for _, pair in comparisons.loc[comparisons['Screen Passed']].iterrows():
                a, b = pair['Ticker 1'], pair['Ticker 2']
                logs = np.log(formation[[a, b]])
                for dependent, independent in [(a, b), (b, a)]:
                    row = pair.to_dict() | {'A': dependent, 'B': independent,
                                           'Observations': len(logs), 'Status': 'OK'}
                    try:
                        row.update(fit_direction(logs, dependent, independent))
                    except (ValueError, np.linalg.LinAlgError, Warning) as error:
                        row['Status'] = str(error)
                    rows.append(row)
            columns = list(comparisons.columns) + ['A', 'B', 'Observations', 'Alpha', 'Beta',
                'Spread Mean', 'Spread Std', 'EG Statistic', 'EG p-value',
                'EG 1% Critical Value', 'EG 5% Critical Value', 'ADF Lags', 'ADF Observations', 'EG Passed']
            result = {'directions': pd.DataFrame(rows).reindex(columns=columns),
                      'comparisons': comparisons, 'eligibility': eligibility,
                      'formation_last': formation.iloc[-1]}
            temporary = path.with_suffix('.tmp')
            pd.to_pickle(result, temporary)
            temporary.replace(path)
            for name in ('directions', 'comparisons', 'eligibility'):
                atomic_csv(result[name], self.cache_folder / f'{key}_{name}.csv', index=False)
            print(f'Cached formation {key}: {len(rows)} directional fits', flush=True)
            return result

    @staticmethod
    def select(directions, corr, eg):
        critical = 'EG 1% Critical Value' if eg == 0.01 else 'EG 5% Critical Value'
        passed = directions.loc[(directions['Status'] == 'OK') &
            (directions['Correlation'] > corr) &
            (directions['EG Statistic'] < directions[critical])]
        return (passed.sort_values(['EG p-value', 'A', 'B'])
                .drop_duplicates(['Ticker 1', 'Ticker 2']).sort_values(['A', 'B']).copy())

    def trading_prices(self, tickers, dates):
        with self._lock:
            for ticker in tickers:
                if ticker not in self._raw_cache:
                    self._raw_cache[ticker] = read_training_series(self.raw / f'{ticker}.csv')
            result = pd.DataFrame({t: self._raw_cache[t].reindex(dates) for t in tickers}, index=dates)
        if not (np.isfinite(result) & result.gt(0)).all().all():
            bad = result.columns[~(np.isfinite(result) & result.gt(0)).all()].tolist()
            raise ValueError(f'Missing or invalid raw trading prices: {bad}; selected pairs were not dropped')
        return result

    def complete(self, p):
        folder = self.folder / parameter_id(p)
        required = ['parameters.json', 'trades.csv', 'portfolio_daily.csv', 'selected_pairs.csv',
                    'window_summary.csv', 'pair_daily.csv.gz', 'summary.csv']
        marker = folder / 'status.json'
        return (marker.exists() and json.loads(marker.read_text()).get('status') == 'complete'
                and all((folder / name).is_file() for name in required))

    def run_batch(self, formation_months, trading_months, z_values=Z_GRID):
        requested = [dict(zip(PARAMETER_NAMES, (formation_months, trading_months, corr, eg, *z)))
                     for corr, eg, z in product(CORRELATION_GRID, EG_GRID, z_values)]
        if all(self.complete(p) for p in requested):
            return
        schedule = self.schedule(formation_months, trading_months)
        prepared = [(w.to_dict(), self.formation(w)) for _, w in schedule.iterrows()]
        for entry, exit_, stop in z_values:
            started = time.perf_counter()
            states = []
            for corr, eg in product(CORRELATION_GRID, EG_GRID):
                p = dict(zip(PARAMETER_NAMES, (formation_months, trading_months, corr, eg, entry, exit_, stop)))
                if self.complete(p):
                    continue
                folder = self.folder / parameter_id(p)
                folder.mkdir(exist_ok=True)
                write_json(folder / 'parameters.json', p | {'run_id': self.run_id,
                    'cost_bps_per_leg': self.cost_bps, 'initial_capital': self.initial_capital})
                write_json(folder / 'status.json', {'status': 'running'})
                atomic_csv(schedule, folder / 'windows.csv', index=False)
                states.append({'p': p, 'folder': folder, 'capital': self.initial_capital,
                               'daily': [], 'trades': [], 'selected': [], 'windows': []})
            if not states:
                continue
            try:
                for window, cached in prepared:
                    dates = interval(self.prices, window['Trading Start'], window['Trading End Exclusive']).index
                    selections = [self.select(cached['directions'], s['p']['correlation_threshold'],
                                              s['p']['eg_significance']) for s in states]
                    union = pd.concat(selections).drop_duplicates(['A', 'B'])
                    tickers = sorted(set(union['A']) | set(union['B']))
                    trading = self.trading_prices(tickers, dates)
                    unit_results = {}
                    for _, pair in union.iterrows():
                        unit_results[pair['A'], pair['B']] = backtest_pair(
                            pair, trading, cached['formation_last'], 1.0, self.cost_bps,
                            entry_z=entry, exit_z=exit_, stop_z=stop)
                    for state, selected in zip(states, selections):
                        capital = state['capital']
                        allocation = capital / len(selected) if len(selected) else 0
                        accounts, trades_parts = [], []
                        folder = state['folder']
                        for _, pair in selected.iterrows():
                            daily, trades = scale_result(unit_results[pair['A'], pair['B']], allocation)
                            trades = enrich_trades(trades, daily, trading, pair)
                            trades.insert(0, 'Window', window['Window'])
                            accounts.append(daily)
                            trades_parts.append(trades)
                            # One compressed audit file per combination, with every pair's daily holdings.
                            audit = daily.assign(Window=window['Window'], A=pair['A'], B=pair['B'])
                            audit_path = folder / 'pair_daily.csv.gz'
                            audit.to_csv(audit_path, mode='a', header=not audit_path.exists(), compression='gzip')
                        trades = (pd.concat(trades_parts, ignore_index=True) if trades_parts
                                  else pd.DataFrame(columns=['Window', *TRADE_COLUMNS, *EXTRA_TRADE_COLUMNS]))
                        portfolio = combine_accounts(accounts, dates, capital)
                        metrics = performance_metrics(portfolio, trades, capital, self.treasury_yields)
                        state['windows'].append(window | metrics | {'Selected Pairs': len(selected),
                            'Initial Capital': capital, 'Final Capital': portfolio['Equity'].iloc[-1],
                            'Eligible Stocks': int(cached['eligibility']['Eligible'].sum())})
                        state['daily'].append(portfolio.assign(Window=window['Window']))
                        state['trades'].append(trades)
                        state['selected'].append(selected.assign(Window=window['Window']))
                        state['capital'] = float(portfolio['Equity'].iloc[-1])
                for state in states:
                    self.save_result(state, time.perf_counter() - started)
                print(f'Formation {formation_months}, trading {trading_months}, z={entry}/{exit_}/{stop}: '
                      f'saved {len(states)} combinations', flush=True)
            except Exception as error:
                for state in states:
                    if not self.complete(state['p']):
                        write_json(state['folder'] / 'status.json', {'status': 'failed', 'error': str(error)})
                raise

    def save_result(self, state, elapsed):
        daily = pd.concat(state['daily'])
        trades = pd.concat(state['trades'], ignore_index=True)
        daily['Gross Equity'] = daily['Equity'] + daily['Costs ($)'].cumsum()
        expected = self.prices.index[self.prices.index >= COMMON_START]
        if not daily.index.equals(expected) or not daily.index.is_unique:
            raise AssertionError('Grid must cover identical evaluation sessions exactly once')
        np.testing.assert_allclose(self.initial_capital * (1 + daily['Net Return']).cumprod(),
                                   daily['Equity'], rtol=1e-9)
        np.testing.assert_allclose(daily['Costs ($)'].sum(), trades['Costs ($)'].sum(), atol=1e-6)
        np.testing.assert_allclose(daily['Equity'].iloc[-1] - self.initial_capital,
                                   trades['Net P/L ($)'].sum(), atol=1e-6)
        windows = pd.DataFrame(state['windows'])
        summary = state['p'] | performance_metrics(daily, trades, self.initial_capital, self.treasury_yields) | {
            'Status': 'complete', 'Windows': len(windows), 'Trading Sessions': len(daily),
            'First Trading Date': daily.index.min(), 'Last Trading Date': daily.index.max(),
            'Average Selected Pairs': windows['Selected Pairs'].mean(),
            'Days With Exposure': int(daily['Active Pairs'].gt(0).sum()),
            'Average Holding Sessions': trades['Holding Sessions'].mean(),
            'Stop Exit Rate': trades['Exit Reason'].eq('Stop loss').mean() if len(trades) else np.nan,
            'Profitable Windows': windows['Cumulative Return'].gt(0).mean(),
            'Batch Runtime Seconds': elapsed, 'Output Folder': str(state['folder'])}
        folder = state['folder']
        atomic_csv(daily, folder / 'portfolio_daily.csv')
        atomic_csv(trades, folder / 'trades.csv', index=False)
        atomic_csv(pd.concat(state['selected'], ignore_index=True), folder / 'selected_pairs.csv', index=False)
        atomic_csv(windows, folder / 'window_summary.csv', index=False)
        atomic_csv(pd.DataFrame([summary]), folder / 'summary.csv', index=False)
        if not (folder / 'pair_daily.csv.gz').exists():
            pd.DataFrame(columns=['Date', 'Window', 'A', 'B', 'Position', 'Equity']).to_csv(
                folder / 'pair_daily.csv.gz', index=False)
        write_json(folder / 'status.json', {'status': 'complete'})

    def summary(self):
        rows = []
        for p in parameter_grid():
            folder = self.folder / parameter_id(p)
            if self.complete(p):
                rows.append(pd.read_csv(folder / 'summary.csv').iloc[0].to_dict())
            else:
                marker = folder / 'status.json'
                status = json.loads(marker.read_text()) if marker.exists() else {'status': 'pending'}
                rows.append(p | {'Status': status['status'], 'Error': status.get('error'),
                                 'Output Folder': str(folder)})
        result = pd.DataFrame(rows)
        if 'Sharpe Ratio' in result:
            result = result.sort_values(['Sharpe Ratio', *PARAMETER_NAMES],
                ascending=[False, *([True] * len(PARAMETER_NAMES))], na_position='last')
        atomic_csv(result, self.folder / 'grid_summary.csv', index=False)
        return result.reset_index(drop=True)

    def run(self, max_workers=2, window_settings=None, z_values=Z_GRID):
        if self.prices is None:
            self.load_data()
        if not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError('max_workers must be a positive integer')
        settings = window_settings or [(f, t) for f, t in product(FORMATION_GRID, TRADING_GRID) if t <= f]
        # Incomplete audit files are rebuilt; completed combinations are left intact.
        for f, t in settings:
            for corr, eg, z in product(CORRELATION_GRID, EG_GRID, z_values):
                p = dict(zip(PARAMETER_NAMES, (f, t, corr, eg, *z)))
                if not self.complete(p):
                    audit = self.folder / parameter_id(p) / 'pair_daily.csv.gz'
                    if audit.exists():
                        audit.unlink()
        failures = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            pending = {pool.submit(self.run_batch, f, t, z_values): (f, t) for f, t in settings}
            for future in as_completed(pending):
                setting = pending[future]
                try:
                    future.result()
                    print(f'Completed/resumed formation={setting[0]}, trading={setting[1]}', flush=True)
                except Exception as error:
                    failures.append((setting, str(error)))
                    for corr, eg, z in product(CORRELATION_GRID, EG_GRID, z_values):
                        p = dict(zip(PARAMETER_NAMES, (*setting, corr, eg, *z)))
                        if not self.complete(p):
                            folder = self.folder / parameter_id(p)
                            folder.mkdir(exist_ok=True)
                            write_json(folder / 'status.json', {'status': 'failed', 'error': str(error)})
                    print(f'FAILED {setting}: {error}', flush=True)
                summary = self.summary()
                print(f"Saved summary: {summary['Status'].value_counts().to_dict()}", flush=True)
        result = self.summary()
        if failures:
            print('Some batches failed. Inspect Error/status.json, fix source data, then rerun to resume.')
        return result


EXTRA_TRADE_COLUMNS = ['Alpha', 'Beta', 'Spread Mean', 'Spread Std', 'Entry Price A',
    'Entry Price B', 'Exit Price A', 'Exit Price B', 'Units A', 'Units B',
    'Holding Sessions', 'Holding Calendar Days']


def scale_result(result, capital):
    daily, trades = (frame.copy() for frame in result)
    for column in ['Equity', 'Before Trade Equity', 'Costs ($)', 'Traded Value ($)',
                   'Units A', 'Units B', 'Gross Equity']:
        daily[column] *= capital
    for column in ['Entry Equity ($)', 'Entry Cost ($)', 'Net P/L ($)', 'Costs ($)']:
        trades[column] = pd.to_numeric(trades[column]) * capital
    return daily, trades


def enrich_trades(trades, daily, prices, pair):
    for column in ['Alpha', 'Beta', 'Spread Mean', 'Spread Std']:
        trades[column] = pair[column]
    for side in ['Entry', 'Exit']:
        dates = pd.DatetimeIndex(trades[f'{side} Date'])
        for leg in ['A', 'B']:
            trades[f'{side} Price {leg}'] = prices[pair[leg]].reindex(dates).to_numpy()
    entries = pd.DatetimeIndex(trades['Entry Date'])
    exits = pd.DatetimeIndex(trades['Exit Date'])
    for leg in ['A', 'B']:
        trades[f'Units {leg}'] = daily[f'Units {leg}'].reindex(entries).to_numpy()
    trades['Holding Sessions'] = daily.index.get_indexer(exits) - daily.index.get_indexer(entries)
    trades['Holding Calendar Days'] = (exits - entries).days
    return trades
