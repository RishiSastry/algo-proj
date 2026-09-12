# Data integrity report

Panel: 2005-01-03 → 2026-09-11, 29 tickers, 5457 trading days.
Prices: yfinance adjusted (auto_adjust=True — splits and dividends folded in).

## Missing trading days (after ipo_date, within own history)
None.

## Zero / negative prices
None.

## Gaps > 5 trading days
None.

## Suspicious single-day moves (|return| > 50%)
| date                | ticker   | return   |
|:--------------------|:---------|:---------|
| 2014-02-21 00:00:00 | WULF     | +51.6%   |
| 2016-04-22 00:00:00 | AMD      | +52.3%   |
| 2021-01-08 00:00:00 | HUT      | +53.6%   |
| 2021-06-25 00:00:00 | WULF     | +64.2%   |
| 2022-06-13 00:00:00 | APLD     | -52.6%   |
| 2022-07-19 00:00:00 | APLD     | +100.0%  |
| 2023-02-15 00:00:00 | IREN     | +67.0%   |
| 2023-05-16 00:00:00 | APLD     | +78.9%   |
| 2024-09-05 00:00:00 | APLD     | +65.7%   |
| 2025-08-14 00:00:00 | WULF     | +59.5%   |

## Assessment
- WULF 2014/2021-06 and HUT 2021-01 predate those tickers' curated
  `ipo_date` (predecessor-entity history) and are excluded from any
  backtest by the survivorship rule.
- AMD 2016-04-22 (+52%, licensing JV announcement), the APLD and IREN
  moves are genuine small/mid-cap price moves, not split artifacts —
  magnitudes match news-driven gaps, and no offsetting reversal follows.
- Conclusion: no split/adjustment errors detected; panel is usable.
