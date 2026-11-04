# Joint parameter grid search — training partition only — zero transaction costs

Test **1,248 feasible combinations**.
Formation: 3, 6, 12, 18 months; trading: 2, 3, 6, 12 months; return correlation: 0.8, 0.9;
Engle–Granger significance: 0.01, 0.05; entry: 1.5, 2.0, 2.5; exit: 0, 0.5;
stop: 3.0, 3.5, 4.0, 4.5.

0 bps per leg at entry and exit

## Top five portfolios by Sharpe ratio

| Rank | Formation (months) | Trading (months) | Correlation threshold | EG significance | Entry z | Exit z | Stop z |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 18 | 6 | 0.8 | 0.01 | 1.5 | 0.5 | 4.0 |
| 2 | 18 | 6 | 0.8 | 0.01 | 2.0 | 0.5 | 4.0 |
| 3 | 18 | 6 | 0.8 | 0.01 | 2.0 | 0.0 | 4.0 |
| 4 | 18 | 6 | 0.8 | 0.01 | 1.5 | 0.0 | 4.0 |
| 5 | 6 | 2 | 0.9 | 0.05 | 1.5 | 0.0 | 4.5 |

| Rank | Cumulative return | Annualized return | Annualized volatility | Sharpe ratio | Maximum drawdown | Trades | Win rate | Average P/L per trade ($) | Average holding (sessions) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 18.61% | 2.42% | 2.48% | 0.3594 | 3.50% | 212 | 63.21% | 87.78 | 27.31 |
| 2 | 17.31% | 2.26% | 2.11% | 0.3474 | 3.01% | 153 | 56.21% | 113.11 | 28.62 |
| 3 | 17.56% | 2.29% | 2.23% | 0.3424 | 3.68% | 146 | 54.11% | 120.27 | 32.82 |
| 4 | 18.45% | 2.40% | 2.70% | 0.3237 | 4.40% | 191 | 60.21% | 96.57 | 33.73 |
| 5 | 17.85% | 2.33% | 2.56% | 0.3133 | 3.13% | 413 | 60.29% | 43.22 | 14.67 |

# Explore the best sharpe zero cost protfoilo

## Portfolio performance

| Metric | Result |
| --- | --- |
| Total return | 18.61% |
| Maximum drawdown | -3.50% |
| Completed trades | 212 |
| Trade win rate | 63.2% |
| Median holding sessions | 19 |

### Cumulative return, trailing return and drawdown

![Cumulative return, trailing return and drawdown](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/portfolio_performance.png)

## Annual performance

| Year | Return | Portfolio P&L ($) | Completed trades | Win rate | Partial year |
| --- | --- | --- | --- | --- | --- |
| 2016 | -1.04% | $-1,044.68 | 29 | 48.3% | Yes |
| 2017 | 1.64% | $1,619.77 | 18 | 66.7% | No |
| 2018 | 2.15% | $2,163.60 | 34 | 55.9% | No |
| 2019 | 0.40% | $405.99 | 24 | 62.5% | No |
| 2020 | 5.46% | $5,633.88 | 30 | 70.0% | No |
| 2021 | 6.40% | $6,961.36 | 42 | 78.6% | No |
| 2022 | 5.45% | $6,302.17 | 21 | 71.4% | No |
| 2023 | -2.81% | $-3,433.72 | 14 | 35.7% | Yes |

### Annual return and trade count

![Annual return and trade count](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/annual_performance.png)

### Monthly return heatmap

![Monthly return heatmap](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/monthly_returns.png)

## Trade outcomes

### Trade profit, loss and holding time

![Trade profit, loss and holding time](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/trade_outcomes.png)

## Losing trades by exit reason

| Exit reason | Losing trades | Share (%) |
| --- | --- | --- |
| Stop loss | 52 | 66.7% |
| Window end | 22 | 28.2% |
| Mean reversion | 4 | 5.1% |

| Exit reason | Loss ($) | Share of total losses (%) | Portfolio return contribution (pp) |
| --- | --- | --- | --- |
| Stop loss | $19,799.09 | 89.0% | -19.80 |
| Window end | $2,338.98 | 10.5% | -2.34 |
| Mean reversion | $115.40 | 0.5% | -0.12 |

### Losing trade counts and losses

![Losing trade counts and losses](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/losing_trade_exits.png)

## Top ten pair contributions

| Pair | P&L ($) | Trades | Selected windows |
| --- | --- | --- | --- |
| MCO / SPGI | $4,129.11 | 5 | 1 |
| MLM / VMC | $2,120.12 | 8 | 2 |
| LUV / UAL | $1,961.61 | 4 | 2 |
| ALK / DAL | $1,842.42 | 1 | 1 |
| QRVO / SWKS | $1,503.45 | 2 | 1 |
| AEP / ED | $1,314.70 | 7 | 2 |
| AFL / L | $1,202.17 | 3 | 1 |
| AWK / NEE | $939.50 | 3 | 1 |
| HST / KIM | $882.08 | 1 | 1 |
| CCL / RCL | $860.92 | 2 | 1 |

### Largest and smallest pair contributions

![Largest and smallest pair contributions](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/pair_contributions.png)

## Profit concentration

| Remove best | Number removed | Removed profit ($) | Share of all positive profits | Share of net portfolio profit | Remaining profit ($) | Remaining profit / initial capital |
| --- | --- | --- | --- | --- | --- | --- |
| Trades | 1 | $2,062.95 | 5.0% | 11.1% | $16,545.41 | 16.55% |
| Trades | 5 | $7,601.37 | 18.6% | 40.8% | $11,006.98 | 11.01% |
| Trades | 10 | $12,247.22 | 30.0% | 65.8% | $6,361.13 | 6.36% |
| Pairs | 1 | $4,129.11 | 13.2% | 22.2% | $14,479.24 | 14.48% |
| Pairs | 5 | $11,556.71 | 37.0% | 62.1% | $7,051.64 | 7.05% |
| Pairs | 10 | $16,756.08 | 53.7% | 90.0% | $1,852.27 | 1.85% |

### Profit after removing the biggest winners

![Profit after removing the biggest winners](outputs/trade_history_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/profit_concentration.png)

## Ten most profitable trades

| Pair | Entry Date | Exit Date | Net P/L ($) | Exit Reason |
| --- | --- | --- | --- | --- |
| LUV / UAL | 2022-10-20 | 2022-12-16 | $2,062.95 | Mean reversion |
| ALK / DAL | 2022-07-01 | 2022-10-20 | $1,842.42 | Mean reversion |
| MCO / SPGI | 2020-03-18 | 2020-03-20 | $1,297.33 | Mean reversion |
| LUV / UAL | 2022-07-22 | 2022-08-02 | $1,217.91 | Mean reversion |
| MCO / SPGI | 2020-03-25 | 2020-04-02 | $1,180.76 | Mean reversion |
| QRVO / SWKS | 2022-09-01 | 2022-10-11 | $1,042.05 | Mean reversion |
| MLM / VMC | 2018-04-26 | 2018-05-04 | $989.24 | Mean reversion |
| ALK / UAL | 2022-01-21 | 2022-02-10 | $891.32 | Mean reversion |
| HST / KIM | 2021-01-26 | 2021-02-17 | $882.08 | Mean reversion |
| CFG / PNC | 2019-02-08 | 2019-03-08 | $841.16 | Mean reversion |

## Stock exposure and overlap

| Metric | Result |
| --- | --- |
| Days with any overlap | 517 / 1799 (28.7%) |
| Days with same-direction overlap | 507 / 1799 (28.2%) |
| Stocks with same-direction overlap | 19 |
| Maximum pairs holding one stock | 5 |

## Largest same-direction stock exposures

| Date | Stock | Pairs | Long pairs | Short pairs | Net exposure ($) | Net exposure / equity (%) | Gross exposure / equity (%) | Pairs held |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2017-02-16 | ETR | 3 | 3 | 0 | $25,352.41 | +25.44% | 25.44% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-13 | ETR | 3 | 3 | 0 | $25,070.21 | +25.26% | 25.26% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-10 | ETR | 3 | 3 | 0 | $24,955.24 | +25.17% | 25.17% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-08 | ETR | 3 | 3 | 0 | $24,875.11 | +25.10% | 25.10% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-09 | ETR | 3 | 3 | 0 | $24,735.75 | +24.96% | 24.96% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-14 | ETR | 3 | 3 | 0 | $24,662.58 | +24.89% | 24.89% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-06 | ETR | 3 | 3 | 0 | $24,666.07 | +24.88% | 24.88% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-15 | ETR | 3 | 3 | 0 | $24,655.62 | +24.87% | 24.87% | AEP / ETR, ES / ETR, ETR / WEC |
| 2017-02-07 | ETR | 3 | 3 | 0 | $24,624.27 | +24.85% | 24.85% | AEP / ETR, ES / ETR, ETR / WEC |
| 2016-12-01 | USB | 5 | 0 | 5 | $-20,261.55 | -20.46% | 20.46% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-30 | USB | 5 | 0 | 5 | $-19,951.94 | -20.11% | 20.11% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-25 | USB | 5 | 0 | 5 | $-19,871.52 | -20.00% | 20.00% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-23 | USB | 5 | 0 | 5 | $-19,843.38 | -19.95% | 19.95% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-21 | USB | 5 | 0 | 5 | $-19,815.22 | -19.93% | 19.93% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-18 | USB | 5 | 0 | 5 | $-19,795.12 | -19.90% | 19.90% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-29 | USB | 5 | 0 | 5 | $-19,742.85 | -19.86% | 19.86% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-22 | USB | 5 | 0 | 5 | $-19,714.70 | -19.82% | 19.82% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-28 | USB | 5 | 0 | 5 | $-19,662.43 | -19.78% | 19.78% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-14 | USB | 5 | 0 | 5 | $-19,594.08 | -19.70% | 19.70% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |
| 2016-11-15 | USB | 5 | 0 | 5 | $-19,582.01 | -19.68% | 19.68% | FITB / USB, KEY / USB, MTB / USB, RF / USB, USB / ZION |

# Industry performance — best Sharpe zero-cost portfolio

## Industry returns and risk

| Industry Group | PnL ($) | Contribution (pp) | Sleeve total return | CAGR | Volatility | Sharpe | Max drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Consumer Services | $1,919.30 | +1.92 | 21.29% | 2.74% | 4.07% | 0.2984 | 5.03% |
| Financial Services | $5,147.65 | +5.15 | 16.93% | 2.22% | 2.56% | 0.2687 | 4.41% |
| Materials | $2,120.12 | +2.12 | 12.66% | 1.68% | 2.93% | 0.0536 | 3.65% |
| Banks | $545.80 | +0.55 | 11.70% | 1.56% | 3.31% | 0.0106 | 5.43% |
| Energy | $1,159.60 | +1.16 | 6.07% | 0.83% | 6.76% | -0.1032 | 12.91% |
| Semiconductors & Semiconductor Equipment | $1,353.76 | +1.35 | 6.08% | 0.83% | 2.48% | -0.2805 | 8.23% |
| Utilities | $769.33 | +0.77 | 6.40% | 0.87% | 2.02% | -0.3242 | 3.70% |
| Consumer Durables & Apparel | $219.59 | +0.22 | -0.26% | -0.04% | 4.00% | -0.3904 | 9.19% |
| Transportation | $2,800.41 | +2.80 | 0.26% | 0.04% | 3.65% | -0.4086 | 8.66% |
| Insurance | $1,202.17 | +1.20 | 6.23% | 0.85% | 1.41% | -0.4782 | 2.53% |
| Food, Beverage & Tobacco | $471.73 | +0.47 | 6.60% | 0.90% | 1.01% | -0.6225 | 1.66% |
| Capital Goods | $7.14 | +0.01 | -1.42% | -0.20% | 2.59% | -0.6667 | 7.54% |
| Equity Real Estate Investment Trusts (REITs) | $681.21 | +0.68 | -0.21% | -0.03% | 2.27% | -0.6862 | 6.04% |
| Media & Entertainment | $318.76 | +0.32 | 2.09% | 0.29% | 0.86% | -1.4447 | 0.94% |
| Commercial  & Professional Services | $-108.22 | -0.11 | -1.92% | -0.27% | 0.89% | -2.0146 | 2.34% |

![Industry Sharpe and portfolio contribution](outputs/industry_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/industry_sharpe_and_contribution.png)

## Industry trading activity

| Industry Group | Trades | Unique pairs | Traded windows | Win rate | Profit factor | Median holding sessions | Coverage screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Consumer Services | 8 | 3 | 3 | 87.5% | 65.66 | 18 | No |
| Financial Services | 16 | 10 | 4 | 75.0% | 7.65 | 16 | No |
| Materials | 8 | 1 | 2 | 87.5% | 4.13 | 18 | No |
| Banks | 48 | 21 | 11 | 56.2% | 1.10 | 20 | Yes |
| Energy | 6 | 4 | 3 | 83.3% | 1.89 | 55 | No |
| Semiconductors & Semiconductor Equipment | 5 | 4 | 3 | 60.0% | 3.14 | 27 | No |
| Utilities | 80 | 43 | 14 | 56.2% | 1.12 | 18 | Yes |
| Consumer Durables & Apparel | 5 | 3 | 3 | 60.0% | 1.17 | 22 | No |
| Transportation | 9 | 5 | 4 | 66.7% | 1.74 | 14 | No |
| Insurance | 3 | 1 | 1 | 100.0% | inf | 37 | No |
| Food, Beverage & Tobacco | 2 | 1 | 1 | 100.0% | inf | 26 | No |
| Capital Goods | 5 | 3 | 3 | 60.0% | 1.01 | 18 | No |
| Equity Real Estate Investment Trusts (REITs) | 6 | 4 | 2 | 66.7% | 1.66 | 18 | No |
| Media & Entertainment | 10 | 2 | 4 | 70.0% | 9.87 | 18 | No |
| Commercial  & Professional Services | 1 | 1 | 1 | 0.0% | 0.00 | 59 | No |

## Industry sleeve growth

![Industry sleeves and portfolio growth](outputs/industry_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/industry_sleeve_growth.png)

## Industry returns by trading window

| Window | Consumer Services | Financial Services | Materials | Banks | Energy | Semiconductors & Semiconductor Equipment | Utilities | Consumer Durables & Apparel | Transportation | Insurance | Food, Beverage & Tobacco | Capital Goods | Equity Real Estate Investment Trusts (REITs) | Media & Entertainment | Commercial  & Professional Services |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.00% | 0.00% | 0.00% | -1.47% | 0.00% | 0.00% | -0.61% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 2 | 0.00% | 0.00% | 0.00% | 2.92% | 0.00% | 0.00% | -0.12% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 3 | 2.60% | 0.00% | 0.00% | -1.90% | 0.00% | 0.00% | 3.03% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 4 | 0.00% | 0.00% | 14.42% | 0.90% | 0.00% | 0.00% | -0.05% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 5 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | -0.93% | 1.69% | 0.00% | 0.00% | 0.00% | 0.00% | -3.37% | 1.27% | 0.00% |
| 6 | 0.00% | 0.00% | 0.00% | 0.31% | 0.00% | 0.00% | 2.20% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.44% | 0.00% |
| 7 | 0.00% | 0.00% | 0.00% | 6.90% | 0.00% | 0.00% | -1.33% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 8 | 0.00% | 12.01% | 0.00% | 0.00% | 0.00% | 0.00% | -0.21% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 9 | 4.21% | -3.03% | 0.00% | 3.31% | 5.82% | 6.76% | -0.74% | 0.00% | 0.00% | 0.00% | 6.60% | 0.00% | 0.00% | 0.00% | 0.00% |
| 10 | 0.00% | 0.00% | 0.00% | -3.18% | 7.52% | 0.00% | 4.18% | 0.00% | 0.94% | 0.00% | 0.00% | 5.83% | 3.28% | 0.00% | 0.00% |
| 11 | 13.43% | 4.15% | 0.00% | 5.99% | -0.00% | -5.61% | 3.79% | 0.00% | 0.00% | 0.00% | 0.00% | -4.95% | 0.00% | 0.00% | -1.92% |
| 12 | 0.00% | 0.00% | -1.54% | -1.80% | -6.78% | 0.00% | -1.33% | 0.00% | -3.29% | 6.23% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 13 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 5.27% | 0.00% | 3.01% | 9.78% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| 14 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | -1.66% | -4.78% | -6.44% | 0.00% | 0.00% | -2.00% | 0.00% | 0.40% | 0.00% |
| 15 | 0.00% | 3.36% | 0.00% | -0.30% | 0.00% | 0.00% | 0.24% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | -0.03% | 0.00% |

![Industry returns by trading window](outputs/industry_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/industry_window_returns.png)

## Trade exits by sector

| Sector | End of window | Mean reversion | Stop loss | Total trades |
| --- | --- | --- | --- | --- |
| Energy | 2 | 3 | 1 | 6 |
| Materials | 1 | 6 | 1 | 8 |
| Industrials | 5 | 6 | 4 | 15 |
| Consumer Discretionary | 3 | 8 | 2 | 13 |
| Consumer Staples | 0 | 2 | 0 | 2 |
| Health Care | 0 | 0 | 0 | 0 |
| Financials | 11 | 40 | 16 | 67 |
| Information Technology | 1 | 2 | 2 | 5 |
| Communication Services | 2 | 8 | 0 | 10 |
| Utilities | 13 | 41 | 26 | 80 |
| Real Estate | 1 | 3 | 2 | 6 |

![Trade exits by sector](outputs/industry_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/sector_exit_type_pies.png)

# Spread plots for every completed trade

See PDF.

# Next-open execution — zero transaction costs

Notebook 8 compares next-close and next-open execution using the same selected pairs and parameters, before transaction costs. Next-open execution reduced cumulative return from 18.61% to 14.63% and Sharpe from 0.359 to 0.158.

## Execution comparison

| Execution | Sharpe Ratio | Cumulative Return | Annualized Return | Annualized Volatility | Maximum Drawdown | Number of Trades | Win Rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Next close | 0.359 | 18.61% | 2.42% | 2.48% | 3.50% | 212 | 63.2% |
| Next open | 0.158 | 14.63% | 1.93% | 2.55% | 3.79% | 212 | 66.0% |

## Annual returns (2016 and 2023 are partial years)

| Year | Next close | Next open |
| --- | --- | --- |
| 2016 | -1.04% | -1.11% |
| 2017 | 1.64% | 1.47% |
| 2018 | 2.15% | 1.83% |
| 2019 | 0.40% | 0.51% |
| 2020 | 5.46% | 3.62% |
| 2021 | 6.40% | 5.16% |
| 2022 | 5.45% | 5.24% |
| 2023 | -2.81% | -2.68% |

## Portfolio growth

![Next-close and next-open portfolio growth](outputs/next_open_execution_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/execution_comparison.png)

# Continuous Kalman portfolio — zero transaction costs

Notebook 9 reselects pairs every six months using an 18-month formation period and updates the hedge model with a continuous Kalman filter. The training-period portfolio returned 4.77%, with a Sharpe ratio of −0.850.

## Portfolio statistics

| Metric | Rolling EG / continuous Kalman |
| --- | --- |
| Cumulative Return | 4.77% |
| Annualized Return | 0.66% |
| Annualized Volatility | 1.03% |
| Annualized Risk-Free Return | 1.53% |
| Sharpe Ratio | -0.850 |
| Maximum Drawdown | 0.73% |
| Number of Trades | 141 |
| Win Rate | 57.45% |
| Average P/L per Trade ($) | $33.84 |
| Average Return per Trade | 0.10% |
| Turnover (x) | 34.01 |

# Factor-adjusted portfolio returns — zero transaction costs

Notebook 10 checks how much of the saved best portfolio’s returns remains after accounting for market, oil, size and value factors. Estimated annual alpha is about 1.04–1.08%, but all three 95% confidence intervals include zero. The rolling comparison estimates factor exposures from the preceding 252 observations; these are attribution results, rather than returns from an executed hedge.

## Portfolio factor-model statistics

| Model | Sessions | R squared | Alpha annual (arithmetic) | Alpha 95% lower | Alpha 95% upper | Alpha HAC p-value | Residual annual volatility | Adjusted mean / vol (annual) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SP500 + oil | 1753 | 0.28% | 1.08% | -0.84% | 2.99% | 0.2703 | 2.50% | 0.430 |
| Fama-French 3 | 1753 | 0.27% | 1.04% | -0.89% | 2.97% | 0.2913 | 2.50% | 0.416 |
| Fama-French 3 + oil | 1753 | 0.59% | 1.08% | -0.85% | 3.00% | 0.2729 | 2.50% | 0.431 |

## Portfolio factor coefficients

| Model | Term | Coefficient | HAC std error | HAC t | p-value | 95% lower | 95% upper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SP500 + oil | const | 0.000043 | 0.000039 | 1.102 | 0.2703 | -0.000033 | 0.000119 |
| SP500 + oil | SP500-RF | 0.004937 | 0.004671 | 1.057 | 0.2905 | -0.004218 | 0.014092 |
| SP500 + oil | Oil | -0.002275 | 0.001683 | -1.352 | 0.1764 | -0.005573 | 0.001023 |
| Fama-French 3 | const | 0.000041 | 0.000039 | 1.055 | 0.2913 | -0.000035 | 0.000118 |
| Fama-French 3 | Mkt-RF | 0.004089 | 0.004648 | 0.880 | 0.3790 | -0.005021 | 0.013199 |
| Fama-French 3 | SMB | -0.003664 | 0.010017 | -0.366 | 0.7146 | -0.023297 | 0.015970 |
| Fama-French 3 | HML | 0.006801 | 0.005013 | 1.357 | 0.1749 | -0.003024 | 0.016626 |
| Fama-French 3 + oil | const | 0.000043 | 0.000039 | 1.096 | 0.2729 | -0.000034 | 0.000119 |
| Fama-French 3 + oil | Mkt-RF | 0.006130 | 0.004955 | 1.237 | 0.2161 | -0.003583 | 0.015842 |
| Fama-French 3 + oil | SMB | -0.004235 | 0.010213 | -0.415 | 0.6784 | -0.024251 | 0.015782 |
| Fama-French 3 + oil | HML | 0.008572 | 0.004999 | 1.715 | 0.0864 | -0.001226 | 0.018370 |
| Fama-French 3 + oil | Oil | -0.002816 | 0.001717 | -1.640 | 0.1010 | -0.006182 | 0.000550 |

## S&P 500 and oil adjustment

![S&P 500 and oil adjustment](outputs/factor_residual_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/SP500_+_oil_returns.png)

## Fama–French three-factor adjustment

![Fama–French three-factor adjustment](outputs/factor_residual_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/Fama-French_3_returns.png)

## Fama–French three factors and oil

![Fama–French three factors and oil](outputs/factor_residual_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/Fama-French_3_+_oil_returns.png)

## Rolling factor adjustment

| Model | Sessions | Adjusted mean annual | Adjusted mean / vol (annual) | Forecast error mean annual |
| --- | --- | --- | --- | --- |
| SP500 + oil | 1501 | 1.49% | 0.561 | -0.33% |
| Fama-French 3 | 1501 | 1.10% | 0.410 | -0.68% |
| Fama-French 3 + oil | 1501 | 1.22% | 0.454 | -0.65% |

![Rolling factor-adjusted returns](outputs/factor_residual_analysis_zero_cost/cb64c19613e1e11beb71/formation_months_18_trading_months_6_correlation_threshold_0.8_eg_significance_0.01_entry_z_1.5_exit_z_0.5_stop_z_4/rolling_adjusted_returns.png)

## Stock-level factor summary

| Model | Stocks | Median R squared | Median annual alpha | Minimum sessions |
| --- | --- | --- | --- | --- |
| Fama-French 3 | 99 | 45.76% | 1.68% | 1753 |
| Fama-French 3 + oil | 99 | 47.68% | 1.78% | 1753 |
| SP500 + oil | 99 | 38.31% | 2.18% | 1753 |

## Top 15 stocks by explained variation — Fama–French three factors and oil

| Stock | Sessions | R squared | Alpha annual (arithmetic) | Alpha HAC p-value |
| --- | --- | --- | --- | --- |
| JPM | 1753 | 76.85% | 6.05% | 0.2531 |
| BAC | 1753 | 76.70% | 3.40% | 0.5956 |
| RF | 1753 | 76.00% | 8.27% | 0.2088 |
| AMP | 1753 | 75.97% | 9.43% | 0.1776 |
| C | 1753 | 75.97% | -7.53% | 0.2311 |
| FITB | 1753 | 75.11% | 1.10% | 0.8789 |
| PNC | 1753 | 74.96% | 0.60% | 0.9197 |
| CFG | 1753 | 74.19% | 2.03% | 0.7736 |
| L | 1753 | 73.08% | -2.17% | 0.6664 |
| KEY | 1753 | 72.46% | -0.90% | 0.9082 |
| TFC | 1753 | 72.31% | -4.29% | 0.5540 |
| USB | 1753 | 72.12% | -2.77% | 0.6318 |
| MS | 1753 | 71.99% | 8.31% | 0.2045 |
| HBAN | 1753 | 71.19% | 2.16% | 0.7549 |
| WFC | 1753 | 69.74% | -4.70% | 0.5090 |
