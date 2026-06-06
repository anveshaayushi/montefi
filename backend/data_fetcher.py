# data_fetcher.py — fixed for yfinance 0.2.x on Python 3.13
import time
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Optional


def fetch_closing_prices(ticker: str, period: str = "5y") -> Optional[pd.Series]:
    try:
        # Download single ticker
        data = yf.download(ticker, period=period, interval="1d",
                           progress=False, auto_adjust=True)

        if data is None or data.empty:
            print(f"[data_fetcher] Empty response for {ticker}")
            return None

        # Flatten MultiIndex columns if present (newer yfinance versions)
        # e.g. ("Close", "AAPL") -> "Close"
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        if "Close" not in data.columns:
            print(f"[data_fetcher] No Close column for {ticker}. Columns: {list(data.columns)}")
            return None

        close = data["Close"]

        # Ensure it's a Series not a scalar
        if not isinstance(close, pd.Series):
            close = pd.Series([close])

        close = close.dropna()

        if len(close) < 30:
            print(f"[data_fetcher] Too few rows for {ticker}: {len(close)}")
            return None

        print(f"[data_fetcher] {ticker}: {len(close)} rows OK")
        return close

    except Exception as e:
        print(f"[data_fetcher] Exception for {ticker}: {e}")
        return None


def fetch_portfolio_prices(tickers: List[str]):
    """
    Returns (DataFrame, fetch_time_ms).
    Key fix: download ALL tickers at once using yf.download(tickers joined by space).
    This avoids the scalar issue completely and is also faster.
    """
    t0 = time.perf_counter()

    try:
        # Download all tickers at once — yfinance handles multi-ticker properly
        tickers_str = " ".join(tickers)
        data = yf.download(tickers_str, period="5y", interval="1d",
                           progress=False, auto_adjust=True)

        if data is None or data.empty:
            raise ValueError(f"No data returned for tickers: {tickers}")

        # For multi-ticker download, columns are MultiIndex: (field, ticker)
        # Extract just "Close" prices
        if isinstance(data.columns, pd.MultiIndex):
            # Get Close prices for all tickers
            if "Close" in data.columns.get_level_values(0):
                df = data["Close"]
            else:
                raise ValueError(f"No Close prices in data. Columns: {list(data.columns)}")
        else:
            # Single ticker — columns are flat
            if "Close" not in data.columns:
                raise ValueError(f"No Close column. Got: {list(data.columns)}")
            df = data[["Close"]].rename(columns={"Close": tickers[0]})

        # Ensure DataFrame (not Series)
        if isinstance(df, pd.Series):
            df = df.to_frame(name=tickers[0])

        # Drop rows with any NaN
        df = df.dropna()

        if df.empty:
            raise ValueError("Price matrix empty after dropping NaN rows")

        # Ensure column names match requested tickers
        print(f"[data_fetcher] Portfolio matrix: {df.shape}, columns: {list(df.columns)}")

        ms = round((time.perf_counter() - t0) * 1000, 2)
        return df, ms

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to fetch portfolio prices: {e}")


def fetch_current_price(ticker: str) -> Optional[float]:
    try:
        stock = yf.Ticker(ticker.upper())
        price = stock.fast_info.last_price
        if price is not None and not np.isnan(float(price)):
            return float(price)
        # Fallback: last close from recent history
        hist = stock.history(period="2d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
    except Exception as e:
        print(f"[data_fetcher] Price fetch failed for {ticker}: {e}")
        return None


def fetch_benchmark_prices(period: str = "5y") -> Optional[pd.Series]:
    try:
        data = yf.download("SPY", period=period, interval="1d",
                           progress=False, auto_adjust=True)
        if data is None or data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        return data["Close"].dropna()
    except Exception as e:
        print(f"[data_fetcher] SPY fetch failed: {e}")
        return None