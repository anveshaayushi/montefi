# simulator.py — fixed for multi-ticker yfinance download
import time
import numpy as np
from typing import List, Dict
from config import SIMULATION_COUNT
from data_fetcher import fetch_portfolio_prices
from metrics import calculate_daily_returns, run_all_metrics


def run_simulation(tickers: List[str], weights: List[float],
                   initial_investment: float = 10000,
                   years: int = 1, simulations: int = None) -> Dict:

    n    = simulations or SIMULATION_COUNT
    days = years * 252
    total_start = time.perf_counter()

    print(f"[simulator] Starting: {tickers} weights={weights} n={n} years={years}")

    # ── Stage 1: Fetch ───────────────────────────────────────────────────────
    prices, fetch_ms = fetch_portfolio_prices(tickers)

    # Reorder columns to match tickers order (yfinance may sort alphabetically)
    available = [t for t in tickers if t in prices.columns]
    if len(available) == 0:
        raise ValueError(f"None of {tickers} found in price data columns: {list(prices.columns)}")

    prices  = prices[available]
    weights_used = [weights[tickers.index(t)] for t in available]

    # Re-normalise weights if any tickers were dropped
    total_w = sum(weights_used)
    weights_used = [w / total_w for w in weights_used]

    print(f"[simulator] Using tickers: {available}, weights: {weights_used}")

    daily_returns_df       = calculate_daily_returns(prices)
    w                      = np.array(weights_used)
    mean_returns           = daily_returns_df.mean().values       # shape (n_tickers,)
    cov_matrix             = daily_returns_df.cov().values        # shape (n_tickers, n_tickers)
    hist_portfolio_returns = (daily_returns_df.values @ w)        # shape (n_days,)

    print(f"[simulator] mean_returns: {mean_returns.shape}, cov: {cov_matrix.shape}")

    # ── Stage 2: Simulation ──────────────────────────────────────────────────
    sim_start    = time.perf_counter()
    final_values = np.zeros(n)
    sim_paths    = np.zeros((n, days))

    for i in range(n):
        sim_daily       = np.random.multivariate_normal(mean_returns, cov_matrix, days)
        portfolio_daily = sim_daily @ w
        portfolio_daily = np.clip(portfolio_daily, -0.5, 0.5)  # guard against overflow
        path            = initial_investment * np.cumprod(1 + portfolio_daily)
        sim_paths[i]    = path
        final_values[i] = path[-1]

    sim_ms = round((time.perf_counter() - sim_start) * 1000, 2)
    print(f"[simulator] Simulation done in {sim_ms}ms")

    # ── Stage 3: Metrics ─────────────────────────────────────────────────────
    metric_dict, metrics_ms = run_all_metrics(
        final_values, sim_paths, hist_portfolio_returns,
        prices, weights_used, initial_investment,
    )

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)
    print(f"[simulator] Total: {total_ms}ms")

    return {
        "simulation_count":    n,
        "tickers":             available,
        "weights":             weights_used,
        "initial_investment":  initial_investment,
        "years":               years,
        "expected_value":      round(float(final_values.mean()), 2),
        "median_value":        round(float(np.median(final_values)), 2),
        "best_case":           round(float(final_values.max()), 2),
        "worst_case":          round(float(final_values.min()), 2),
        "volatility":          round(float(np.std(final_values)), 2),
        "expected_return_pct": round(float((final_values.mean() - initial_investment) / initial_investment * 100), 2),
        "prob_profit_pct":     round(float(np.mean(final_values > initial_investment) * 100), 2),
        **metric_dict,
        "final_values": [round(float(v), 2) for v in final_values[:100]],
        "latency": {
            "data_fetch_ms": fetch_ms,
            "simulation_ms": sim_ms,
            "metrics_ms":    metrics_ms,
            "ai_ms":         None,
            "total_ms":      total_ms,
        },
    }