"""
Stock Market Data Analyzer
==========================
A command-line Python tool that downloads historical stock price data,
computes key statistics (highest/lowest price, moving averages, daily
returns), and visualizes the trend with Matplotlib.

Author : Ruhan Paul
Tools  : Python, Pandas, yfinance, Matplotlib

USAGE
-----
    python stock_analyzer.py --ticker AAPL --period 6mo --ma 20 50

    --ticker   Stock symbol, e.g. AAPL, TCS.NS, RELIANCE.NS, MSFT
    --period   How much history to pull: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    --ma       One or more moving-average windows (days), e.g. 20 50 200
    --csv      (optional) Path to a local CSV instead of downloading

If you don't have an internet connection or yfinance is blocked on your
network, pass --csv path/to/file.csv where the CSV has at least a "Date"
and "Close" column (Open/High/Low/Volume are optional but recommended).
"""

import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. DATA COLLECTION
# ---------------------------------------------------------------------------
def download_stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Downloads historical OHLCV (Open-High-Low-Close-Volume) data for a
    given ticker using the yfinance library (a free wrapper around
    Yahoo Finance's public data).

    Parameters
    ----------
    ticker : str
        Stock symbol, e.g. "AAPL" (Apple) or "TCS.NS" (TCS on NSE India).
    period : str
        Lookback window: "1mo", "3mo", "6mo", "1y", "2y", "5y", "max".

    Returns
    -------
    pd.DataFrame
        Indexed by Date, with columns: Open, High, Low, Close, Volume.
    """
    import yfinance as yf

    print(f"Downloading data for {ticker} (period={period}) ...")
    df = yf.download(ticker, period=period, progress=False)

    if df.empty:
        raise ValueError(
            f"No data returned for '{ticker}'. Check the symbol/period, "
            f"or your internet connection."
        )

    # yfinance sometimes returns MultiIndex columns (Ticker, Field) when
    # downloading a single symbol in recent versions -> flatten them.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    return df


def load_stock_data_from_csv(path: str) -> pd.DataFrame:
    """
    Loads stock data from a local CSV file instead of the internet.
    Expects a "Date" column and at least a "Close" column.
    """
    df = pd.read_csv(path, parse_dates=["Date"])
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    return df


# ---------------------------------------------------------------------------
# 2. ANALYSIS
# ---------------------------------------------------------------------------
def get_highest_lowest(df: pd.DataFrame) -> dict:
    """
    Returns the highest and lowest closing price in the dataset,
    along with the dates on which they occurred.
    """
    highest_price = df["Close"].max()
    lowest_price = df["Close"].min()
    highest_date = df["Close"].idxmax()
    lowest_date = df["Close"].idxmin()

    return {
        "highest_price": round(float(highest_price), 2),
        "highest_date": highest_date,
        "lowest_price": round(float(lowest_price), 2),
        "lowest_date": lowest_date,
    }


def calculate_moving_averages(df: pd.DataFrame, windows=(20, 50)) -> pd.DataFrame:
    """
    Adds one Simple Moving Average (SMA) column per window size.
    A moving average smooths out day-to-day noise so the underlying
    trend is easier to see, e.g. SMA_20 = average close price of the
    trailing 20 trading days.
    """
    for w in windows:
        df[f"SMA_{w}"] = df["Close"].rolling(window=w).mean()
    return df


def calculate_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Daily Return' column: the percentage change in closing
    price from one trading day to the next.
        Daily Return (%) = (Close_today - Close_yesterday) / Close_yesterday * 100
    """
    df["Daily Return"] = df["Close"].pct_change() * 100
    return df


def summarize_returns(df: pd.DataFrame) -> dict:
    """
    Basic descriptive stats on daily returns: average, volatility
    (standard deviation), best day, worst day.
    """
    returns = df["Daily Return"].dropna()
    return {
        "avg_daily_return_pct": round(returns.mean(), 3),
        "volatility_pct": round(returns.std(), 3),
        "best_day": returns.idxmax(),
        "best_day_return_pct": round(returns.max(), 2),
        "worst_day": returns.idxmin(),
        "worst_day_return_pct": round(returns.min(), 2),
    }


# ---------------------------------------------------------------------------
# 3. VISUALIZATION
# ---------------------------------------------------------------------------
def plot_stock_trend(df: pd.DataFrame, ticker: str, ma_windows, save_path=None):
    """
    Plots closing price with moving-average overlays on top, and daily
    returns as a bar chart underneath, on two stacked subplots.
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    # --- Top: Price + Moving Averages ---
    ax1.plot(df.index, df["Close"], label="Close Price", color="black", linewidth=1.5)
    for w in ma_windows:
        col = f"SMA_{w}"
        if col in df.columns:
            ax1.plot(df.index, df[col], label=f"SMA {w}", linewidth=1.2)

    ax1.set_title(f"{ticker} — Price Trend & Moving Averages")
    ax1.set_ylabel("Price")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.3)

    # --- Bottom: Daily Returns ---
    colors = ["green" if r >= 0 else "red" for r in df["Daily Return"].fillna(0)]
    ax2.bar(df.index, df["Daily Return"], color=colors, width=1.0)
    ax2.set_title("Daily Returns (%)")
    ax2.set_ylabel("Return (%)")
    ax2.set_xlabel("Date")
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Plot saved to: {save_path}")
    plt.show()


# ---------------------------------------------------------------------------
# 4. MAIN / CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Stock Market Data Analyzer")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Stock symbol")
    parser.add_argument("--period", type=str, default="6mo", help="History window")
    parser.add_argument(
        "--ma", type=int, nargs="+", default=[20, 50], help="Moving average windows"
    )
    parser.add_argument("--csv", type=str, default=None, help="Local CSV path instead of download")
    parser.add_argument("--save", type=str, default="stock_trend.png", help="Path to save the plot")
    args = parser.parse_args()

    # 1. Get data
    if args.csv:
        df = load_stock_data_from_csv(args.csv)
    else:
        df = download_stock_data(args.ticker, args.period)

    # 2. Analyze
    df = calculate_moving_averages(df, args.ma)
    df = calculate_daily_returns(df)

    price_stats = get_highest_lowest(df)
    return_stats = summarize_returns(df)

    # 3. Report
    print("\n" + "=" * 50)
    print(f"STOCK ANALYSIS REPORT: {args.ticker}")
    print("=" * 50)
    print(f"Highest Close : {price_stats['highest_price']}  on {price_stats['highest_date'].date()}")
    print(f"Lowest Close  : {price_stats['lowest_price']}  on {price_stats['lowest_date'].date()}")
    print(f"Avg Daily Return : {return_stats['avg_daily_return_pct']}%")
    print(f"Volatility (std) : {return_stats['volatility_pct']}%")
    print(f"Best Day  : {return_stats['best_day'].date()}  ({return_stats['best_day_return_pct']}%)")
    print(f"Worst Day : {return_stats['worst_day'].date()} ({return_stats['worst_day_return_pct']}%)")
    print("=" * 50 + "\n")

    # 4. Visualize
    plot_stock_trend(df, args.ticker, args.ma, save_path=args.save)


if __name__ == "__main__":
    sys.exit(main())
