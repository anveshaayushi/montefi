# optimizer_routes.py — portfolio optimization endpoint
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from optimizer import optimize_portfolio

router = APIRouter(tags=["Optimizer"])


class OptimizeRequest(BaseModel):
    tickers:   List[str]
    objective: str = "max_sharpe"   # or "min_variance"


@router.post("/optimize")
def optimize(data: OptimizeRequest):
    try:
        return optimize_portfolio(data.tickers, data.objective)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))