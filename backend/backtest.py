# backtest.py — validate the simulation model against real historical outcomes
import numpy as np
from typing import List, Dict
from config import SIMULATION_COUNT
from data_fetcher import fetch_portfolio_prices
from metrics import calculate_daily_returns


def run_backtest(tickers: List[str], weights: List[float],
                 test_years: int = 1, initial_investment: float = 10000,
                 simulations: int = None) -> Dict:

    n = simulations or SIMULATION_COUNT
    test_days = test_years * 252

    prices, _ = fetch_portfolio_prices(tickers)
    available = [t for t in tickers if t in prices.columns]
    if len(available) == 0:
        raise ValueError(f"None of {tickers} found in price data")
    prices = prices[available]
    weights_used = [weights[tickers.index(t)] for t in available]
    total_w = sum(weights_used)
    weights_used = [w / total_w for w in weights_used]
    w = np.array(weights_used)

    if len(prices) <= test_days + 100:
        raise ValueError("Not enough historical data to backtest with this test window")

    train_prices = prices.iloc[:-test_days]
    test_prices  = prices.iloc[-test_days:]

    # ── Train: estimate the model's stats using ONLY the training window ──
    train_returns = calculate_daily_returns(train_prices)
    mean_returns  = train_returns.mean().values
    cov_matrix    = train_returns.cov().values

    # ── Simulate forward over the test horizon, blind to what actually happened ──
    L = np.linalg.cholesky(cov_matrix)
    Z = np.random.standard_normal((n, test_days, len(mean_returns)))
    sim_daily = mean_returns + Z @ L.T
    portfolio_daily = np.clip(sim_daily @ w, -0.5, 0.5)
    sim_paths = initial_investment * np.cumprod(1 + portfolio_daily, axis=1)
    final_values = sim_paths[:, -1]

    # ── Actual: what really happened during the test window ──
    test_returns = test_prices.pct_change().dropna().values
    actual_portfolio_daily = test_returns @ w
    actual_path = initial_investment * np.cumprod(1 + actual_portfolio_daily)
    actual_final_value = float(actual_path[-1])

    # ── Compare: where does reality fall within the simulated range? ──
    percentile_rank = float((final_values < actual_final_value).mean() * 100)
    well_calibrated  = 10 <= percentile_rank <= 90

    return {
        "tickers":              available,
        "weights":              weights_used,
        "test_years":           test_years,
        "train_window_days":    len(train_prices),
        "test_window_days":     len(test_prices),
        "simulated_p10":        round(float(np.percentile(final_values, 10)), 2),
        "simulated_p50":        round(float(np.percentile(final_values, 50)), 2),
        "simulated_p90":        round(float(np.percentile(final_values, 90)), 2),
        "actual_final_value":   round(actual_final_value, 2),
        "actual_percentile_rank": round(percentile_rank, 1),
        "within_80pct_band":    well_calibrated,
        "verdict": (
            "Model well-calibrated — actual outcome fell within the central 80% of simulated outcomes."
            if well_calibrated else
            "Actual outcome was an outlier relative to the simulated distribution — model may be under/overestimating risk."
        ),
    }