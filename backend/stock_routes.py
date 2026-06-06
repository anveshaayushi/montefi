# stock_routes.py
import time
from fastapi import APIRouter, HTTPException
from data_fetcher import fetch_current_price

router = APIRouter(tags=["Stocks"])


@router.get("/stock/{ticker}")
def get_stock_price(ticker: str):
    t0    = time.perf_counter()
    price = fetch_current_price(ticker.upper())
    ms    = round((time.perf_counter() - t0) * 1000, 2)

    if price is None:
        raise HTTPException(404, detail=f"Could not fetch price for {ticker.upper()}")

    return {"ticker": ticker.upper(), "price": round(price, 2),
            "currency": "USD", "latency_ms": ms}