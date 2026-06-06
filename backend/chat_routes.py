# chat_routes.py — Chatbot with LangChain + Gemini + DuckDuckGo news
# Falls back gracefully to news fetch + rule-based if no Gemini key
import time
import traceback
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from config import GEMINI_API_KEY

router = APIRouter(tags=["Chatbot"])


class ChatMessage(BaseModel):
    role:    str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


# ── News fetcher ─────────────────────────────────────────────────────────────

COMPANY_MAP = {
    "apple": "Apple Inc AAPL stock",
    "aapl":  "Apple Inc AAPL stock",
    "tesla": "Tesla TSLA stock",
    "tsla":  "Tesla TSLA stock",
    "microsoft": "Microsoft MSFT stock",
    "msft":  "Microsoft MSFT stock",
    "google": "Alphabet Google GOOGL stock",
    "googl": "Alphabet Google GOOGL stock",
    "amazon": "Amazon AMZN stock",
    "amzn":  "Amazon AMZN stock",
    "nvidia": "NVIDIA NVDA stock",
    "nvda":  "NVIDIA NVDA stock",
    "meta":  "Meta Platforms META stock",
    "netflix": "Netflix NFLX stock",
    "nflx":  "Netflix NFLX stock",
    "reliance": "Reliance Industries stock India",
    "tata":  "Tata Group stock India",
    "infosys": "Infosys INFY stock",
    "wipro": "Wipro stock India",
    "hdfc":  "HDFC Bank stock India",
}


def fetch_news(company_raw: str) -> list:
    """
    Fetch news using DuckDuckGo Instant Answer API — free, no key needed.
    Returns list of {title, url, source, snippet} dicts.
    """
    # Map to better search query
    query_key = company_raw.lower().strip()
    query = COMPANY_MAP.get(query_key, f"{company_raw} stock financial news")

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MonteFinance/1.0)"}
        url     = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_redirect=1&no_html=1&skip_disambig=1"
        resp    = requests.get(url, headers=headers, timeout=10)
        data    = resp.json()

        results = []

        # Abstract — best single summary
        if data.get("AbstractText"):
            results.append({
                "title":   f"{data.get('Heading', company_raw)} — Overview",
                "snippet": data["AbstractText"][:300],
                "url":     data.get("AbstractURL", ""),
                "source":  data.get("AbstractSource", "Wikipedia"),
            })

        # RelatedTopics — news-like entries
        for topic in data.get("RelatedTopics", [])[:6]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title":   topic["Text"][:100],
                    "snippet": topic["Text"][:200],
                    "url":     topic.get("FirstURL", ""),
                    "source":  "DuckDuckGo",
                })

        # Infobox if available
        if data.get("Infobox"):
            for item in data["Infobox"].get("content", [])[:3]:
                if item.get("label") and item.get("value"):
                    results.append({
                        "title":   f"{item['label']}: {item['value']}",
                        "snippet": f"{item['label']}: {item['value']}",
                        "url":     "",
                        "source":  "DuckDuckGo Infobox",
                    })

        print(f"[chat] Fetched {len(results)} results for '{query}'")
        return results[:5]

    except Exception as e:
        print(f"[chat] News fetch error: {e}")
        return []


def detect_company(message: str) -> Optional[str]:
    """
    Detect if user is asking about a company.
    Returns the company identifier or None.
    """
    msg = message.lower().strip()

    # Trigger phrases
    triggers = [
        "news about", "news on", "news for", "latest on", "latest news",
        "tell me about", "how is", "update on", "report on",
        "what's happening with", "what is happening with",
        "financial news", "stock news", "earnings for",
        "stock price of", "price of",
    ]

    # Direct ticker / company mentions
    known_companies = list(COMPANY_MAP.keys())

    # Check triggers first
    for trigger in triggers:
        if trigger in msg:
            after = msg[msg.find(trigger) + len(trigger):].strip()
            # Get first 1-2 words after trigger
            words = after.split()[:2]
            candidate = words[0] if words else ""
            if candidate in COMPANY_MAP:
                return candidate
            # Even if not in map, return what they said
            if candidate:
                return " ".join(words)

    # Check direct company mentions without trigger
    for company in known_companies:
        if company in msg:
            return company

    return None


def build_news_summary(company: str, news_items: list) -> str:
    """Build a plain-text news summary from fetched items."""
    if not news_items:
        return f"I couldn't fetch live news for '{company}' right now. Try searching on Google Finance or Yahoo Finance for the latest updates."

    summary = f"Here's what I found about **{company.title()}**:\n\n"
    for i, item in enumerate(news_items[:3], 1):
        summary += f"{i}. {item['snippet']}"
        if item.get("url"):
            summary += f"\n   📎 Source: {item['source']} — {item['url']}"
        summary += "\n\n"

    return summary.strip()


# ── Main chat endpoint ────────────────────────────────────────────────────────

@router.post("/chat")
def chat(req: ChatRequest):
    t0 = time.perf_counter()

    # Always check for company news request first (works with or without Gemini)
    company    = detect_company(req.message)
    news_items = []

    if company:
        news_items = fetch_news(company)

    # If Gemini key available — use LangChain for full conversational response
    if GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

            news_context = ""
            if news_items:
                news_context = f"\n\nLive data fetched for '{company}':\n"
                for item in news_items:
                    news_context += f"- {item['snippet']} (Source: {item['source']}, URL: {item['url']})\n"

            system = f"""You are MonteFi's financial assistant — concise, knowledgeable, helpful.
You're embedded in a quantitative portfolio analytics web app.

Platform features:
- Market Intelligence: real-time stock price lookup by ticker
- Portfolio Builder: add stocks, set weights (must total 100%), run Monte Carlo simulation  
- Simulation Results: shows Sharpe ratio, VaR 95%/99%, max drawdown, beta, confidence intervals
- AI Risk Analysis: plain-English interpretation of simulation metrics
- Save/Load Portfolios: persist named portfolios to database
- Light/Dark mode toggle: Sun/Moon icon top-right nav

Keep responses to 3-5 sentences. When citing news, always mention the source.
{news_context}"""

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.4,
                max_output_tokens=400,
            )

            messages = [SystemMessage(content=system)]
            for msg in req.history[-6:]:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))
            messages.append(HumanMessage(content=req.message))

            response = llm.invoke(messages)
            reply    = response.content

            # Append source links clearly
            if news_items:
                reply += "\n\n📰 Sources:"
                for item in news_items[:3]:
                    if item.get("url"):
                        reply += f"\n• {item['source']}: {item['url']}"

            ms = round((time.perf_counter() - t0) * 1000, 2)
            return {"reply": reply, "sources": news_items, "latency_ms": ms,
                    "used_news": bool(news_items), "company": company}

        except Exception as e:
            traceback.print_exc()
            print(f"[chat] Gemini failed, falling back: {e}")
            # Fall through to rule-based below

    # ── Fallback: news fetch + rule-based (no Gemini needed) ─────────────────
    msg = req.message.lower()

    # If we fetched news, return that directly
    if news_items:
        reply = build_news_summary(company, news_items)
        ms    = round((time.perf_counter() - t0) * 1000, 2)
        return {"reply": reply, "sources": news_items, "latency_ms": ms,
                "used_news": True, "company": company}

    # Rule-based for concepts and navigation
    if any(w in msg for w in ["sharpe"]):
        reply = "The Sharpe Ratio measures return per unit of risk. Formula: (Annual Return − Risk Free Rate) / Annual Volatility. Above 1.0 is good, above 2.0 is excellent. MonteFi uses a 5% risk-free rate (US T-bill)."
    elif any(w in msg for w in ["var", "value at risk"]):
        reply = "VaR 95% means: in 95% of simulated scenarios, your loss won't exceed that amount. For example, VaR −12% on a $10,000 portfolio means worst expected loss is $1,200 in 95% of scenarios."
    elif any(w in msg for w in ["beta"]):
        reply = "Beta measures how your portfolio moves vs the S&P 500. Beta 1.0 = moves with market. Beta 1.5 = 50% more volatile. Beta 0.5 = half as volatile. MonteFi calculates beta against SPY ETF."
    elif any(w in msg for w in ["drawdown", "max drawdown"]):
        reply = "Max Drawdown is the largest peak-to-trough decline across all simulated paths. It answers: how bad could the dip get before recovery? MonteFi shows the median max drawdown across 1,000 simulation paths."
    elif any(w in msg for w in ["monte carlo", "simulation"]):
        reply = "Monte Carlo simulation runs 1,000 possible portfolio futures using historical return distributions and covariance between stocks. Results show expected value, bear/base/bull scenarios (p10/p50/p90), and probability of reaching your target."
    elif any(w in msg for w in ["confidence interval", "p10", "p50", "p90", "bear", "bull case"]):
        reply = "Confidence intervals show the range of outcomes: p10 (bear case — worst 10%), p50 (median/base case), p90 (bull case — best 10%). These replace best/worst case which are extreme outliers."
    elif any(w in msg for w in ["save", "load", "portfolio"]):
        reply = "To save a portfolio: build your holdings in Portfolio Builder, then click the 💾 Save button. Give it a name and it's stored in the database. Click 📂 Load to see all saved portfolios and restore any of them."
    elif any(w in msg for w in ["search", "ticker", "price", "stock price"]):
        reply = "Use Market Intelligence at the top of the page. Type any ticker (AAPL, TSLA, NVDA, RELIANCE.NS for Indian stocks) and click Search. The price is fetched live via yfinance — no API key needed."
    elif any(w in msg for w in ["light", "dark", "theme", "mode"]):
        reply = "Click the ☀️/🌙 icon in the top-right navbar to toggle between dark mode (teal accent, dark background) and light mode (cream background, forest green accent)."
    elif any(w in msg for w in ["weight", "allocation", "balance"]):
        reply = "Set stock weights using the sliders in Portfolio Builder. Weights must total exactly 100%. Use Auto-Balance to split equally, or drag sliders manually. The weight indicator turns green when you hit 100%."
    elif any(w in msg for w in ["latency", "speed", "performance", "fast"]):
        reply = "MonteFi tracks latency for every stage: data fetch (yfinance), simulation loop, metrics calculation, and AI analysis. Total latency is returned in every simulation response under the 'latency' key."
    elif any(w in msg for w in ["hi", "hello", "hey", "what can you do", "help"]):
        reply = "Hi! I'm MonteFi's assistant. I can: explain financial metrics (Sharpe, VaR, Beta, Drawdown), fetch company news (try 'news about Tesla'), help you navigate the platform, or interpret simulation results. What do you need?"
    else:
        reply = "I can help with: financial metrics (Sharpe, VaR, Beta, Drawdown), company news ('news about Apple'), navigating MonteFi, or interpreting your simulation results. What would you like to know?"

    ms = round((time.perf_counter() - t0) * 1000, 2)
    return {"reply": reply, "sources": [], "latency_ms": ms,
            "used_news": False, "company": company}