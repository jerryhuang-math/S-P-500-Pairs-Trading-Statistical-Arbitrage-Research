# GICS dataset

The September 12, 2026 enrichment adds **113 tickers**, bringing the mapping to
616 companies. Only the following classification fields were populated for those
tickers:

- `Sector Code` (GICS2) and `Sector`
- `Industry Group Code` (GICS4) and `Industry Group`

Their industry and sub-industry fields remain blank. All 503 pre-existing rows
were preserved byte-for-byte in the enrichment, including their existing finer
classifications. Company names were added to identify the new ticker rows.

`gics2_gics4_sources.csv` records each addition, its source URL, source date when
available, retrieval date, derivation, and any special treatment. Public S&P
400/600 constituent tables supplied most assignments, supplemented by historical
S&P 500 snapshots, S&P announcements, and company/GICS reference publications.
Where a source provides a finer GICS classification, it is rolled up to sector
and industry group using `gics_structure.csv`; finer tags are not saved for the
new companies. Names and codes follow the local March 2023 hierarchy.

These are static classifications, not a point-in-time history. Historical
sources are identified in the source log. In particular, Time Warner (TWX)
was historically classified as Consumer Discretionary / Media (25/2540).
Its assignment here, Communication Services / Media & Entertainment (50/5020),
is an explicit crosswalk to the local hierarchy, not an observed classification
of a currently listed Time Warner security.

Historical ticker identities are retained: BBT means BB&T, not today's Beacon
Financial; TE means TECO Energy; BBBY means the original Bed Bath & Beyond;
FB means Facebook/Meta; LB means historical L Brands. INFO uses IHS Markit's
own historical classification, not its acquirer's classification.

`unmatched_tickers.csv` now means tickers without sector or industry group;
it contains only its header after this enrichment. The download notebook's save
step preserves existing rows (including intentional blanks) and adds only new
tickers, so rerunning it will retain this work. The pair-selection notebook still
requires sub-industry codes; these new rows will not enter that existing screen
unless its grouping logic is separately changed to sector or industry group.
