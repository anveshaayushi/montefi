# portfolio_routes.py — CRUD for portfolios
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import db, Portfolio, Holding, SimulationResult

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


class HoldingSchema(BaseModel):
    ticker: str
    weight: float

class PortfolioCreate(BaseModel):
    name:       str
    holdings:   List[HoldingSchema]
    session_id: str = "default"

class PortfolioUpdate(BaseModel):
    name:     Optional[str]                 = None
    holdings: Optional[List[HoldingSchema]] = None


def _validate_weights(holdings):
    total = sum(h.weight for h in holdings)
    if abs(total - 1.0) > 0.01:
        raise HTTPException(400, detail=f"Weights must sum to 1.0, got {total:.3f}")

def _serialize(p):
    return {
        "id":         p.id,
        "name":       p.name,
        "session_id": p.session_id,
        "holdings":   [{"ticker": h.ticker, "weight": h.weight} for h in p.holdings],
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.post("", status_code=201)
def create_portfolio(data: PortfolioCreate):
    _validate_weights(data.holdings)
    now = datetime.datetime.utcnow()
    with db.atomic():
        p = Portfolio.create(name=data.name, session_id=data.session_id,
                             created_at=now, updated_at=now)
        for h in data.holdings:
            Holding.create(portfolio=p, ticker=h.ticker.upper(), weight=h.weight)
    return _serialize(p)


@router.get("")
def list_portfolios(session_id: str = "default"):
    qs = (Portfolio.select()
          .where(Portfolio.session_id == session_id)
          .order_by(Portfolio.created_at.desc()))
    return [_serialize(p) for p in qs]


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: int):
    try:
        p = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(404, detail="Portfolio not found")

    sims = [
        {
            "id":               s.id,
            "initial_investment": s.initial_investment,
            "years":            s.years,
            "expected_value":   s.expected_value,
            "sharpe_ratio":     s.sharpe_ratio,
            "var_95_pct":       s.var_95_pct,
            "max_drawdown_pct": s.max_drawdown_pct,
            "latency_total_ms": s.latency_total_ms,
            "ai_analysis":      s.ai_analysis,
            "run_at":           s.run_at.isoformat(),
        }
        for s in (SimulationResult.select()
                  .where(SimulationResult.portfolio == p)
                  .order_by(SimulationResult.run_at.desc())
                  .limit(10))
    ]
    result = _serialize(p)
    result["simulation_history"] = sims
    return result


@router.put("/{portfolio_id}")
def update_portfolio(portfolio_id: int, data: PortfolioUpdate):
    try:
        p = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(404, detail="Portfolio not found")

    with db.atomic():
        if data.name:
            p.name = data.name
        if data.holdings is not None:
            _validate_weights(data.holdings)
            Holding.delete().where(Holding.portfolio == p).execute()
            for h in data.holdings:
                Holding.create(portfolio=p, ticker=h.ticker.upper(), weight=h.weight)
        p.updated_at = datetime.datetime.utcnow()
        p.save()
    return {"message": "Updated", "id": portfolio_id}


@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int):
    try:
        p = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(404, detail="Portfolio not found")
    p.delete_instance(recursive=True)
    return {"message": f"Portfolio {portfolio_id} deleted"}