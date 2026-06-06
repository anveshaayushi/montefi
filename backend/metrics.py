# metrics.py — pure financial math, no API calls, no DB
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from config import RISK_FREE_RATE
from data_fetcher import fetch_benchmark_prices


def calculate_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    returns = prices.pct_change().dropna()
    return returns.replace([np.inf, -np.inf], np.nan).dropna()


def calculate_sharpe_ratio(portfolio_daily_returns: np.ndarray) -> float:
    daily_std = np.std(portfolio_daily_returns)
    if daily_std == 0:
        return 0.0
    annual_return     = np.mean(portfolio_daily_returns) * 252
    annual_volatility = daily_std * np.sqrt(252)
    return round(float((annual_return - RISK_FREE_RATE) / annual_volatility), 4)


def calculate_var(final_values: np.ndarray, initial_investment: float) -> Dict:
    returns = (final_values - initial_investment) / initial_investment
    var_95  = float(np.percentile(returns, 5))
    var_99  = float(np.percentile(returns, 1))
    return {
        "var_95_pct":    round(var_95 * 100, 2),
        "var_99_pct":    round(var_99 * 100, 2),
        "var_95_amount": round(var_95 * initial_investment, 2),
        "var_99_amount": round(var_99 * initial_investment, 2),
    }


def calculate_max_drawdown(simulation_paths: np.ndarray) -> float:
    drawdowns = []
    for path in simulation_paths:
        running_max = np.maximum.accumulate(path)
        dd = (path - running_max) / running_max
        drawdowns.append(float(np.min(dd)))
    return round(float(np.median(drawdowns)) * 100, 2)


def calculate_beta(portfolio_daily_returns: np.ndarray) -> Optional[float]:
    try:
        spy_prices = fetch_benchmark_prices()
        if spy_prices is None:
            return None
        spy_returns = spy_prices.pct_change().dropna().values
        min_len     = min(len(portfolio_daily_returns), len(spy_returns))
        port        = portfolio_daily_returns[-min_len:]
        market      = spy_returns[-min_len:]
        cov         = np.cov(port, market)[0][1]
        var         = np.var(market)
        return round(float(cov / var), 4) if var != 0 else None
    except Exception as e:
        print(f"[metrics] Beta failed: {e}")
        return None


def calculate_confidence_intervals(final_values: np.ndarray) -> Dict:
    return {
        "p10": round(float(np.percentile(final_values, 10)), 2),
        "p25": round(float(np.percentile(final_values, 25)), 2),
        "p50": round(float(np.percentile(final_values, 50)), 2),
        "p75": round(float(np.percentile(final_values, 75)), 2),
        "p90": round(float(np.percentile(final_values, 90)), 2),
    }


def calculate_annualised_return(prices: pd.DataFrame, weights: List[float]) -> float:
    w          = np.array(weights)
    total      = (prices.iloc[-1] / prices.iloc[0]).values
    weighted   = float(np.dot(total, w))
    hist_years = len(prices) / 252
    if hist_years == 0:
        return 0.0
    return round((weighted ** (1 / hist_years) - 1) * 100, 2)


def run_all_metrics(final_values, simulation_paths, hist_portfolio_returns,
                    prices, weights, initial_investment):
    """Runs all metrics, returns (dict, elapsed_ms)."""
    t0 = time.perf_counter()
    result = {
        "sharpe_ratio":          calculate_sharpe_ratio(hist_portfolio_returns),
        "var":                   calculate_var(final_values, initial_investment),
        "max_drawdown_pct":      calculate_max_drawdown(simulation_paths),
        "beta":                  calculate_beta(hist_portfolio_returns),
        "confidence_intervals":  calculate_confidence_intervals(final_values),
        "annualised_return_pct": calculate_annualised_return(prices, weights),
    }
    return result, round((time.perf_counter() - t0) * 1000, 2)