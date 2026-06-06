# routes/simulation_routes.py — simulation endpoints only
# Orchestrates: simulator.py (math) + ai_analyst.py (AI) + DB persistence

import json
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from portfolio import Portfolio
from simulation_result import SimulationResult
from simulator import run_simulation
from ai_analyst import generate_portfolio_analysis
from database import db

router = APIRouter(tags=["Simulations"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SimulateByIdRequest(BaseModel):
    portfolio_id:       int
    initial_investment: float = 10000
    years:              int   = 1

class DirectSimulateRequest(BaseModel):
    """Simulate without saving a portfolio — keeps frontend backward compatible."""
    tickers:            List[str]
    weights:            List[float]
    initial_investment: float = 10000
    years:              int   = 1
    target_amount:      float = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/portfolios/{portfolio_id}/simulate")
def simulate_saved_portfolio(portfolio_id: int, req: SimulateByIdRequest):
    """Simulate a saved portfolio. Persists results + AI analysis."""
    try:
        portfolio = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(404, detail="Portfolio not found")

    holdings = list(portfolio.holdings)
    tickers  = [h.ticker for h in holdings]
    weights  = [h.weight for h in holdings]

    results = run_simulation(
        tickers=tickers, weights=weights,
        initial_investment=req.initial_investment, years=req.years,
    )

    # AI analysis — timed separately
    ai_text, ai_ms = generate_portfolio_analysis(results, tickers, weights)

    # Update latency object with AI time and new total
    latency = results.get("latency", {})
    latency["ai_ms"]    = ai_ms
    latency["total_ms"] = round(latency.get("total_ms", 0) + ai_ms, 2)
    results["latency"]  = latency

    # Persist to DB
    ci  = results.get("confidence_intervals", {})
    var = results.get("var", {})
    sim = SimulationResult.create(
        portfolio             = portfolio,
        initial_investment    = req.initial_investment,
        years                 = req.years,
        simulation_count      = results.get("simulation_count", 1000),
        expected_value        = results.get("expected_value", 0),
        expected_return_pct   = results.get("expected_return_pct"),
        sharpe_ratio          = results.get("sharpe_ratio"),
        var_95_pct            = var.get("var_95_pct"),
        var_99_pct            = var.get("var_99_pct"),
        max_drawdown_pct      = results.get("max_drawdown_pct"),
        beta                  = results.get("beta"),
        prob_profit_pct       = results.get("prob_profit_pct"),
        annualised_return_pct = results.get("annualised_return_pct"),
        latency_data_fetch_ms = latency.get("data_fetch_ms"),
        latency_simulation_ms = latency.get("simulation_ms"),
        latency_metrics_ms    = latency.get("metrics_ms"),
        latency_ai_ms         = ai_ms,
        latency_total_ms      = latency.get("total_ms"),
        confidence_intervals_json = json.dumps(ci),
        ai_analysis           = ai_text,
    )

    results["ai_analysis"]   = ai_text
    results["simulation_id"] = sim.id
    return results


@router.post("/simulate")
def simulate_direct(req: DirectSimulateRequest):
    """
    Simulate without saving a portfolio.
    Backward compatible with original frontend — just POST tickers + weights.
    """
    if abs(sum(req.weights) - 1.0) > 0.01:
        raise HTTPException(400, detail="Weights must sum to 1.0")
    if len(req.tickers) != len(req.weights):
        raise HTTPException(400, detail="Tickers and weights count mismatch")

    results = run_simulation(
        tickers=req.tickers, weights=req.weights,
        initial_investment=req.initial_investment, years=req.years,
    )

    ai_text, ai_ms = generate_portfolio_analysis(results, req.tickers, req.weights)

    latency = results.get("latency", {})
    latency["ai_ms"]    = ai_ms
    latency["total_ms"] = round(latency.get("total_ms", 0) + ai_ms, 2)
    results["latency"]  = latency
    results["ai_analysis"] = ai_text
    return results


@router.get("/portfolios/{portfolio_id}/simulations")
def get_simulation_history(portfolio_id: int):
    """All past simulation runs for a portfolio, with latency data."""
    try:
        portfolio = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(404, detail="Portfolio not found")

    sims = SimulationResult.select() \
        .where(SimulationResult.portfolio == portfolio) \
        .order_by(SimulationResult.run_at.desc())

    return [{
        "id":                   s.id,
        "initial_investment":   s.initial_investment,
        "years":                s.years,
        "expected_value":       s.expected_value,
        "expected_return_pct":  s.expected_return_pct,
        "sharpe_ratio":         s.sharpe_ratio,
        "var_95_pct":           s.var_95_pct,
        "var_99_pct":           s.var_99_pct,
        "max_drawdown_pct":     s.max_drawdown_pct,
        "beta":                 s.beta,
        "prob_profit_pct":      s.prob_profit_pct,
        "annualised_return_pct":s.annualised_return_pct,
        "ai_analysis":          s.ai_analysis,
        "latency": {
            "data_fetch_ms":  s.latency_data_fetch_ms,
            "simulation_ms":  s.latency_simulation_ms,
            "metrics_ms":     s.latency_metrics_ms,
            "ai_ms":          s.latency_ai_ms,
            "total_ms":       s.latency_total_ms,
        },
        "run_at": s.run_at.isoformat(),
    } for s in sims]