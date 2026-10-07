# backtest_routes.py — backtesting endpoint
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backtest import run_backtest

router = APIRouter(tags=["Backtest"])


class BacktestRequest(BaseModel):
    tickers:    List[str]
    weights:    List[float]
    test_years: int = 1


@router.post("/backtest")
def backtest(data: BacktestRequest):
    try:
        return run_backtest(data.tickers, data.weights, data.test_years)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))