# MonteFi

**MonteFi** is a full-stack quantitative portfolio analytics platform that simulates future portfolio performance using Monte Carlo methods. Users can build a weighted stock portfolio, fetch real-time and historical pricing data, and run large-scale simulations to evaluate expected returns, risk, and best/worst-case outcomes over a chosen time horizon — backed by an AI analyst that explains the numbers in plain English.

## What It Does

- **Portfolio construction** — add tickers and assign weights to build a custom portfolio
- **Historical data ingestion** — pulls ~15–20 years of daily stock data via `yfinance`
- **Monte Carlo simulation** — generates thousands of simulated future market scenarios using a multivariate normal model derived from historical return statistics and correlations
- **Risk & performance metrics**:
  - Sharpe Ratio
  - Value at Risk (95% / 99%)
  - Maximum Drawdown
  - Beta vs. S&P 500 (SPY)
  - Confidence intervals on projected returns
  - Probability of profit
- **AI portfolio analyst** — LangChain + Gemini generate a natural-language breakdown of simulation results and portfolio risk
- **Persistence** — saved portfolios and simulation runs stored via Peewee ORM (SQLite)
- **Performance tracking** — per-stage latency tracking across the simulation pipeline
- **Interactive frontend** — dark/light mode, real-time charts, and smooth animated transitions for exploring simulation outcomes

## Tech Stack

**Backend**
- FastAPI
- NumPy, Pandas
- Peewee ORM (SQLite)
- yfinance (market data)
- LangChain + Google Gemini (AI analysis)

**Frontend**
- React (Vite)
- Tailwind CSS
- Recharts (data visualization)
- Framer Motion (animations)

## How It Works

1. The user selects tickers and assigns portfolio weights.
2. The backend fetches historical daily price data for all tickers simultaneously via yfinance.
3. Historical returns, volatilities, and cross-asset correlations are computed.
4. A multivariate normal model uses these statistics to generate thousands of simulated future price paths over the chosen horizon.
5. Risk and performance metrics are computed from the simulated outcomes.
6. Results are visualized on the frontend, and an LLM-generated summary explains the portfolio's risk/return profile in plain language.

## Project Structure

```
montefi/
├── backend/      # FastAPI app: data ingestion, simulation engine, metrics, AI analyst
├── frontend/     # React + Vite app: portfolio builder and results dashboard
├── requirements.txt
└── README.md
```

## Getting Started

### Backend
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Notes

- Built as a deep-dive into quantitative finance concepts (Monte Carlo simulation, risk metrics) paired with a modern full-stack architecture.
- Designed as a resume and interview project showcasing backend system design, statistical modeling, and AI integration.
