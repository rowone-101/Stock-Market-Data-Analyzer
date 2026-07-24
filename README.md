# Stock Market Data Analyzer

A Python tool that downloads historical stock data and analyzes it: highest/lowest
price, moving averages, daily returns, and a visual trend chart. Built with
**Pandas**, **Matplotlib**, and **yfinance**.

## Files
- `stock_analyzer.py` — the full project (data download, analysis, plotting, CLI)
- `sample_AAPL_data.csv` — synthetic sample data so you can test the script instantly,
  without needing internet access, while you're demoing it
- `demo_output.png` — example chart produced by the script


## Usage

**Live data (needs internet):**
```bash
python stock_analyzer.py --ticker AAPL --period 6mo --ma 20 50
```
- `--ticker` — any Yahoo Finance symbol, e.g. `AAPL`, `MSFT`, `TCS.NS`, `RELIANCE.NS`
- `--period` — `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max`
- `--ma` — one or more moving average windows in days

**Offline / sample data:**
```bash
python stock_analyzer.py --csv sample_AAPL_data.csv --ticker DEMO --ma 20 50
```

Either way, the script prints a text report to the console and saves/shows a
two-panel chart (price + moving averages on top, daily returns as a bar chart
below).

## How it works (code walkthrough)

**1. Data collection** — `download_stock_data()` calls `yfinance.download()`,
which hits Yahoo Finance's public data feed and returns a Pandas DataFrame
indexed by date with Open/High/Low/Close/Volume columns. `load_stock_data_from_csv()`
does the same thing from a local file, for offline use.

**2. Highest / lowest price** — `get_highest_lowest()` uses `df["Close"].max()`
and `.idxmax()` (and the `min` equivalents) to find both the price and the date
it occurred on.

**3. Moving average** — `calculate_moving_averages()` uses Pandas'
`.rolling(window=w).mean()`, which computes the average closing price over a
trailing window of `w` trading days. This smooths short-term noise so the
underlying trend (uptrend/downtrend/sideways) is easier to spot. A 20-day MA
crossing above a 50-day MA is a classic "bullish crossover" signal, and vice
versa.

**4. Daily return** — `calculate_daily_returns()` uses `.pct_change()` to
compute the percentage change in closing price from one day to the next:

```
Daily Return (%) = (Close_today − Close_yesterday) / Close_yesterday × 100
```

`summarize_returns()` then derives average return, volatility (standard
deviation of returns — a common risk proxy), and the best/worst single day.

**5. Visualization** — `plot_stock_trend()` builds a two-panel Matplotlib
figure: the top panel overlays closing price with each moving average; the
bottom panel is a green/red bar chart of daily returns (green = gain, red =
loss), sharing the same x-axis (date) so you can visually correlate price
moves with volatility spikes.

## Extending it (good talking points for an interview)
- Swap the simple moving average for an **exponential moving average (EMA)**
  using `.ewm(span=w).mean()`, which weights recent days more heavily.
- Add **RSI** or **Bollinger Bands** as additional technical indicators.
- Add a `--compare` flag to overlay multiple tickers on one chart.
- Persist results to a CSV/SQLite database instead of just printing them.
- Wrap it in a small Streamlit app for an interactive web dashboard.
