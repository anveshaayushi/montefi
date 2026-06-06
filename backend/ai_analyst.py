# ai_analyst.py — LangChain + Gemini, completely isolated
import time
from typing import List, Optional, Dict
from config import GEMINI_API_KEY


def generate_portfolio_analysis(metrics: Dict, tickers: List[str],
                                 weights: List[float]):
    """Returns (analysis_text_or_None, elapsed_ms)."""
    if not GEMINI_API_KEY:
        print("[ai_analyst] GEMINI_API_KEY not set — skipping")
        return None, 0.0

    t0 = time.perf_counter()
    try:
        from langchain.prompts import PromptTemplate
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.output_parsers import StrOutputParser

        template = """You are a quantitative portfolio analyst. Give a concise plain-English
risk summary in 4-5 sentences. Be specific about numbers. No bullet points.

Portfolio: {tickers} — weights {weights}
Investment: ${initial_investment} over {years} year(s)

Metrics:
- Expected value: ${expected_value} ({expected_return_pct}% return)
- Sharpe Ratio: {sharpe_ratio}  (>1.0 good, >2.0 excellent)
- VaR 95%: {var_95_pct}%  (max expected loss 95% of the time)
- VaR 99%: {var_99_pct}%
- Max Drawdown: {max_drawdown_pct}%
- Beta vs S&P 500: {beta}  (1.0 = moves with market)
- Prob. of profit: {prob_profit_pct}%
- Bear (p10): ${p10} | Base (p50): ${p50} | Bull (p90): ${p90}

Assess: is Sharpe strong or weak? What does VaR mean practically? Is beta high or low risk?"""

        prompt = PromptTemplate(
            input_variables=[
                "tickers","weights","initial_investment","years",
                "expected_value","expected_return_pct","sharpe_ratio",
                "var_95_pct","var_99_pct","max_drawdown_pct","beta",
                "prob_profit_pct","p10","p50","p90",
            ],
            template=template,
        )
        llm   = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                                        google_api_key=GEMINI_API_KEY,
                                        temperature=0.3)
        chain = prompt | llm | StrOutputParser()

        ci  = metrics.get("confidence_intervals", {})
        var = metrics.get("var", {})

        text = chain.invoke({
            "tickers":             ", ".join(tickers),
            "weights":             ", ".join([f"{w*100:.0f}%" for w in weights]),
            "initial_investment":  metrics.get("initial_investment", 10000),
            "years":               metrics.get("years", 1),
            "expected_value":      metrics.get("expected_value", "N/A"),
            "expected_return_pct": metrics.get("expected_return_pct", "N/A"),
            "sharpe_ratio":        metrics.get("sharpe_ratio", "N/A"),
            "var_95_pct":          var.get("var_95_pct", "N/A"),
            "var_99_pct":          var.get("var_99_pct", "N/A"),
            "max_drawdown_pct":    metrics.get("max_drawdown_pct", "N/A"),
            "beta":                metrics.get("beta", "N/A"),
            "prob_profit_pct":     metrics.get("prob_profit_pct", "N/A"),
            "p10":                 ci.get("p10", "N/A"),
            "p50":                 ci.get("p50", "N/A"),
            "p90":                 ci.get("p90", "N/A"),
        })
        return text, round((time.perf_counter() - t0) * 1000, 2)

    except Exception as e:
        print(f"[ai_analyst] Failed: {e}")
        return None, round((time.perf_counter() - t0) * 1000, 2)