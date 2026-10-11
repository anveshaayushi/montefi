# MonteFi

A quantitative portfolio analytics platform. Build a portfolio, run a Monte Carlo simulation on it, get risk metrics, optimize the weights, backtest the model, and ask questions about uploaded filings with RAG.

**Stack:** FastAPI · NumPy / Pandas / SciPy · PostgreSQL (Docker) · Peewee ORM · LangChain + Gemini · React (Create React App)

---

## Features

- **Monte Carlo simulation**: 1,000+ correlated portfolio paths per run. Correlation comes from a Cholesky decomposition of the covariance matrix, and all draws are generated in one vectorized NumPy call (simulation stage 45.6 ms → 17.1 ms, about 2.7x faster than the loop version).
- **Risk metrics**: Sharpe ratio, VaR (95% / 99%), median max drawdown, beta vs. SPY, p10 / p50 / p90 outcome bands.
- **Portfolio optimizer**: mean-variance optimization (max Sharpe or min variance) with SciPy `trust-constr` and long-only constraints.
- **Backtesting**: train/test split. Simulates forward from the training period and checks where the realized outcome falls in the simulated distribution (p10–p90 band).
- **RAG over documents**: paragraph chunking with overlap, Gemini embeddings, cosine-similarity retrieval in NumPy, answers grounded in the retrieved text with source citations.
- **AI risk analysis**: plain-English summary of the simulation metrics, written by Gemini via LangChain.
- **Chat assistant**: LangChain + Gemini, with news lookup and a rule-based fallback when the LLM is unavailable.
- **Save / load portfolios** in PostgreSQL.

## Project structure

```
montefi/
├── backend/
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── config.py            # loads backend/.env
│   ├── database.py          # PostgreSQL connection + table creation
│   ├── simulator.py         # vectorized Monte Carlo
│   ├── metrics.py           # Sharpe, VaR, drawdown, beta
│   ├── optimizer.py         # mean-variance optimizer
│   ├── backtest.py          # train/test backtest
│   ├── rag.py               # chunking, embeddings, retrieval, grounded answers
│   ├── ai_analyst.py        # Gemini risk summary
│   ├── *_routes.py          # API routers
│   ├── portfolio.py, holding.py, simulation_result.py, document_chunk.py   # Peewee models
│   └── requirements.txt
└── frontend/                # React (Create React App)
```

## Setup

### Prerequisites
Python 3.11+, Node.js 18+, Docker Desktop, and a [Gemini API key](https://aistudio.google.com/).

### 1. Start PostgreSQL (Docker)
Postgres runs in a container on host port **5433** (not 5432, to avoid clashing with a native Postgres install).

```bash
docker run --name montefi-postgres -e POSTGRES_PASSWORD=<your_password> -e POSTGRES_DB=<your_db_name> -p 5433:5432 -d postgres
```

After a reboot, start it again with `docker start montefi-postgres` (Docker Desktop must be running).

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

Create `backend/.env`:

```
GEMINI_API_KEY=your_key_here
DB_NAME=<your_db_name>
DB_USER=postgres
DB_PASSWORD=<your_password>
DB_HOST=127.0.0.1
DB_PORT=5433
```

Run it:

```bash
python main.py
```

Interactive API docs (Swagger) are at `http://localhost:8000/docs`. Tables are created automatically on startup.

### 3. Frontend

```bash
cd frontend
npm install
npm start
```

The app opens at `http://localhost:3000`. The backend allows CORS from that origin.

## Key endpoints

Full list and request schemas are in Swagger (`/docs`).

| Method | Path | Purpose |
|---|---|---|
| POST | `/portfolios/{id}/simulate` | Run Monte Carlo, metrics and AI analysis for a saved portfolio |
| POST | `/optimize` | Optimal weights. Body: `{tickers, objective}` |
| POST | `/backtest` | Train/test backtest. Body: `{tickers, weights, test_years}` |
| POST | `/documents/ingest` | Chunk, embed and store a document |
| POST | `/documents/ask` | Ask a question, answered from stored documents with sources |
| POST | `/chat` | Chat assistant |

## Notes and limitations

- The AI analysis call to Gemini dominates `/simulate` latency (tens of seconds). The numerical pipeline itself takes milliseconds.
- Optimizer and backtest results are in-sample / historical and are not investment advice.
- Embeddings are stored as JSON in Postgres and searched with NumPy. This is fine for small document sets; a vector index (e.g. pgvector) would be the next step at scale.

## Roadmap

- LangGraph-based multi-step analyst agent
- Full `docker-compose` deployment (backend + frontend + Postgres)
- Auth, automated tests, and splitting the large frontend component
