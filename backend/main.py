# main.py — entry point only
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from database import connect_db
from stock_routes import router as stock_router
from portfolio_routes import router as portfolio_router
from simulation_routes import router as simulation_router
from chat_routes import router as chat_router

app = FastAPI(title="MonteFi API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_latency(request: Request, call_next):
    t0       = time.perf_counter()
    response = await call_next(request)
    ms       = round((time.perf_counter() - t0) * 1000, 2)
    print(f"[LATENCY] {request.method} {request.url.path} → {response.status_code} | {ms}ms")
    response.headers["X-Response-Time-Ms"] = str(ms)
    return response

connect_db()

app.include_router(stock_router)
app.include_router(portfolio_router)
app.include_router(simulation_router)
app.include_router(chat_router)

@app.get("/")
def home():
    return {
        "status": "MonteFi API v2.0 running",
        "docs":   "/docs",
        "endpoints": {
            "stock":          "GET  /stock/{ticker}",
            "simulate":       "POST /simulate",
            "portfolios":     "CRUD /portfolios",
            "simulate_saved": "POST /portfolios/{id}/simulate",
            "sim_history":    "GET  /portfolios/{id}/simulations",
            "chat":           "POST /chat",
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)