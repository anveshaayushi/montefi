import os
from pathlib import Path

def _load():
    p = Path(__file__).parent / ".env"
    print(f"[config] Reading: {p}")
    with open(p, "rb") as f:
        for line in f.read().decode("utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()
                print(f"[config] Loaded {k.strip()}")

_load()

GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
DB_PATH          = os.environ.get("DB_PATH", "montefi.db")
RISK_FREE_RATE   = float(os.environ.get("RISK_FREE_RATE", "0.05"))
SIMULATION_COUNT = int(os.environ.get("SIMULATION_COUNT", "1000"))

print(f"[config] KEY={'SET ✓' if GEMINI_API_KEY else 'NOT SET'}")