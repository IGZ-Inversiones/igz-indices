#!/usr/bin/env python3
"""Actualiza S&P 500 (SPY) y Nasdaq-100 (QQQ) a retorno total y los guarda en
data/indices.json, que la herramienta IGZ lee desde GitHub (raw).
Fuente: Yahoo Finance (adjusted close = dividendos reinvertidos + splits)."""
import json, urllib.request, datetime, os, time

UA = {"User-Agent": "Mozilla/5.0 (compatible; IGZ-indices/1.0)"}
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]

def fetch_yahoo(sym):
    last = None
    for h in HOSTS:
        try:
            url = f"https://{h}/v8/finance/chart/{sym}?range=10y&interval=1d"
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.load(resp)
            r = d["chart"]["result"][0]
            ts = r["timestamp"]
            adj = r["indicators"]["adjclose"][0]["adjclose"]
            out = []
            for t, a in zip(ts, adj):
                if a is None:
                    continue
                dt = datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
                out.append((dt, float(a)))
            if out:
                return out
        except Exception as e:
            last = e
            time.sleep(2)
    raise RuntimeError(f"No pude bajar {sym}: {last}")

def normalize(series):
    base = series[0][1]
    return [[d, round(v / base * 100, 4)] for d, v in series]

def main():
    os.makedirs("data", exist_ok=True)
    data = {
        "updated": datetime.date.today().isoformat(),
        "nota": "niveles a retorno total, primer dato = 100",
        "spy": normalize(fetch_yahoo("SPY")),
        "qqq": normalize(fetch_yahoo("QQQ")),
    }
    with open("data/indices.json", "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("OK · SPY", len(data["spy"]), "· QQQ", len(data["qqq"]), "· updated", data["updated"])

if __name__ == "__main__":
    main()
