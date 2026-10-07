# optimizer.py — portfolio optimization (efficient frontier)
import numpy as np
from scipy.optimize import minimize, LinearConstraint
from typing import List, Dict
from config import RISK_FREE_RATE
from data_fetcher import fetch_portfolio_prices
from metrics import calculate_daily_returns


def _portfolio_stats(w: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray):
    ret = float(w @ mean_returns) * 252
    vol = float(np.sqrt(w @ cov_matrix @ w)) * np.sqrt(252)
    return ret, vol


def optimize_portfolio(tickers: List[str], objective: str = "max_sharpe") -> Dict:
    prices, _ = fetch_portfolio_prices(tickers)
    available = [t for t in tickers if t in prices.columns]
    if len(available) < 2:
        raise ValueError("Need at least 2 valid tickers to optimize")

    prices = prices[available]
    daily_returns_df = calculate_daily_returns(prices)
    mean_returns = daily_returns_df.mean().values
    cov_matrix   = daily_returns_df.cov().values
    n = len(available)

    def neg_sharpe(w):
        ret, vol = _portfolio_stats(w, mean_returns, cov_matrix)
        if vol == 0:
            return 0
        return -(ret - RISK_FREE_RATE) / vol

    def portfolio_variance(w):
        return float(w @ cov_matrix @ w)

    objective_fn = portfolio_variance if objective == "min_variance" else neg_sharpe

    x0          = np.ones(n) / n
    bounds      = [(0.0, 1.0)] * n
    constraint  = LinearConstraint(np.ones(n), 1, 1)   # weights must sum to 1

    result = minimize(objective_fn, x0, method="trust-constr",
                      bounds=bounds, constraints=[constraint])

    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    weights = result.x
    ret, vol = _portfolio_stats(weights, mean_returns, cov_matrix)
    sharpe   = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0

    return {
        "tickers":            available,
        "optimal_weights":    [round(float(w), 4) for w in weights],
        "expected_return_pct": round(ret * 100, 2),
        "expected_volatility_pct": round(vol * 100, 2),
        "sharpe_ratio":       round(float(sharpe), 4),
        "objective":          objective,
    }