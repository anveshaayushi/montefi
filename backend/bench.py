import time
import numpy as np
from data_fetcher import fetch_portfolio_prices
from metrics import calculate_daily_returns, calculate_max_drawdown
from optimizer import optimize_portfolio
from backtest import run_backtest
from config import RISK_FREE_RATE

tickers = ['AAPL', 'MSFT', 'GOOGL']
w = np.ones(3) / 3
prices, _ = fetch_portfolio_prices(tickers)
r = calculate_daily_returns(prices[tickers])
mean, cov = r.mean().values, r.cov().values
n, days = 1000, 252

def loop_sim():
    fv = np.zeros(n); paths = np.zeros((n, days))
    for i in range(n):
        s = np.random.multivariate_normal(mean, cov, days)
        p = np.clip(s @ w, -0.5, 0.5)
        paths[i] = 10000 * np.cumprod(1 + p); fv[i] = paths[i][-1]
    return paths

def vec_sim():
    L = np.linalg.cholesky(cov)
    Z = np.random.standard_normal((n, days, 3))
    p = np.clip((mean + Z @ L.T) @ w, -0.5, 0.5)
    return 10000 * np.cumprod(1 + p, axis=1)

def loop_dd(paths):
    d = []
    for path in paths:
        m = np.maximum.accumulate(path)
        d.append(float(np.min((path - m) / m)))
    return round(float(np.median(d)) * 100, 2)

def med_ms(fn, *a, runs=7):
    t = []
    for _ in range(runs):
        s = time.perf_counter(); fn(*a); t.append((time.perf_counter() - s) * 1000)
    return round(float(np.median(t)), 2)

paths = vec_sim()
print("SIM   loop ms:", med_ms(loop_sim), "| vectorized ms:", med_ms(vec_sim))
print("DD    loop ms:", med_ms(loop_dd, paths), "| vectorized ms:", med_ms(calculate_max_drawdown, paths))

ret = float(w @ mean) * 252
vol = float(np.sqrt(w @ cov @ w)) * np.sqrt(252)
eq_sharpe = (ret - RISK_FREE_RATE) / vol
opt = optimize_portfolio(tickers, "max_sharpe")
print("SHARPE equal-weight:", round(eq_sharpe, 4), "| optimized:", opt["sharpe_ratio"])

tests = [(['AAPL','MSFT'], [.6,.4]), (['AAPL','GOOGL'], [.5,.5]),
         (['MSFT','GOOGL'], [.5,.5]), (['AAPL','MSFT','GOOGL'], [.4,.3,.3]),
         (['NVDA','AMZN'], [.5,.5])]
hits = 0
for t, wt in tests:
    res = run_backtest(t, wt)
    hits += res["within_80pct_band"]
    print("BACKTEST", t, res["actual_percentile_rank"], res["within_80pct_band"])
print(f"BACKTEST within band: {hits}/{len(tests)}")