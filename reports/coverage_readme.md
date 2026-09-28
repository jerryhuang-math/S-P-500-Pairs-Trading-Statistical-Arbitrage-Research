# Stock Coverage Analysis

We aim to find low-coverage stocks and treat with the missing data problems. 

We first download the entire data of the historical S&P 500. We find out that some of the dataset is longer than we need, since some stocks are only in the S&P 500 for a particular period of time. We only need to take that period of time and check the stock coverage enough in that period of time. 

We want to check whether each stock has enough price data **while it was in the S&P 500**. Raw downloads come from `data/historical`. After membership is loaded, the shortened files are saved to `data/Filter_historical`; all later coverage checks use those filtered files. We use a dataset from a GitHub repository and load historical S&P 500 membership, and then shorten the data to match the S&P 500 membership.

A raw file may contain prices from before a stock entered the S&P 500 or after it left. Those extra dates can make actual coverage appear higher than theoretical coverage. We therefore filter first and look for low coverage afterward. The membership file tells us which stocks belonged to the index on each date. 

And then we run through all those data and see the coverage, and we flag the stocks below 90% coverage. There are, in total, 17. We review the result and discover that different companies have different situations. Some are because of the historical tag on the ticker, and some others are because of ticker reuse or simply because Yahoo Finance has no correct record on this. 

We want to find another alternative data source that records all historical companies and stock prices.