import time
import requests

URL = "http://localhost:8000/portfolios"
requests.get(URL)  # warm-up call, ignored

server_ms, total_ms = [], []
for _ in range(30):
    t = time.perf_counter()
    r = requests.get(URL)
    total_ms.append((time.perf_counter() - t) * 1000)
    server_ms.append(float(r.headers["x-response-time-ms"]))

server_ms.sort(); total_ms.sort()
print("server-side median ms:", server_ms[15])
print("round-trip median ms: ", round(total_ms[15], 2))