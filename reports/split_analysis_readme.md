# Split analysis

This notebook checks whether downloaded closing prices remain reasonably smooth around stock split dates. A large jump may mean that a file needs manual review before pair selection.

It reads the original CSV files from `data/historical` and gets split dates from Yahoo Finance. It does not change or save any data.

We define the split check function. For each split inside a stock's downloaded date range, the function compares the last close before the split with the first close on or after it. The split date is provided by Yfinance. Yahoo normally supplies split-adjusted historical prices, so the values should usually be fairly close.

`Smooth = False` is a warning to investigate the event; it does not automatically mean the data is wrong. It is where the adjusted close price of two days differ by more than 20%. Normal market moves or unusual corporate actions can also create a large change.

We run through every stocks for the dataset and checked for 158 split events. There are 6 events that reaches the warning threshold (20% price change).

We investigate into the six figaaed events. EQT's abnormal jump is due to non-consecutive trading days. This is normal. DHR, XRX, VTR are due to the Yfinance incorrect handling of spin off. MNST is due to the inconsistent dataset of Yfinance, requiring alternative data source. COL is due to historical ticker misuse, which also requres an alternative datas source.