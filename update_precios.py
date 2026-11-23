#!/usr/bin/env python3
"""Genera data/precios.json para la herramienta de carteras IGZ.

Lee tickers.txt (TICKER_LOCAL[=SIMBOLO_YAHOO]) y baja 10 años de precios de
cierre AJUSTADOS (dividendos reinvertidos + splits) de Yahoo Finance.
Todas las series quedan alineadas al calendario de SPY.
Formato:
  {"updated": "AAAA-MM-DD", "fuente": "...", "dates": [...],
   "series": {"AMZN": {"y": "AMZN", "p": [precio|null, ...]}, ...},
   "errores": {"XXX": "motivo"}}
No toca data/indices.json.
"""
import json, urllib.request, datetime, os, time, sys

UA = {"User-Agent": "Mozilla/5.0 (compatible; IGZ-precios/1.0)"}
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
RANGE = "10y"


def leer_tickers(path="tickers.txt"):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            local, _, yahoo = line.partition("=")
            local = local.strip().upper()
            yahoo = (yahoo.strip() or local).upper()
            if local not in [l for l, _ in out]:
                out.append((local, yahoo))
    return out


def fetch_yahoo(sym):
    last = None
    for h in HOSTS:
        for intento in range(2):
            try:
                url = f"https://{h}/v8/finance/chart/{sym}?range={RANGE}&interval=1d&events=div,splits"
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    d = json.load(resp)
                r = d["chart"]["result"][0]
                ts = r["timestamp"]
                adj = r["indicators"]["adjclose"][0]["adjclose"]
                out = {}
                for t, a in zip(ts, adj):
                    if a is None:
                        continue
                    dt = datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
                    out[dt] = float(a)
                if out:
                    return out
                raise RuntimeError("serie vacía")
            except Exception as e:
                last = e
                time.sleep(1.5)
    raise RuntimeError(str(last))


def redondear(x):
    # 6 cifras significativas alcanzan y achican el archivo
    return float(f"{x:.6g}")


def main():
    os.makedirs("data", exist_ok=True)
    tickers = leer_tickers()
    if not any(l == "SPY" for l, _ in tickers):
        tickers.insert(0, ("SPY", "SPY"))
    bajadas, errores = {}, {}
    for local, yahoo in tickers:
        try:
            bajadas[local] = (yahoo, fetch_yahoo(yahoo))
            print(f"ok  {local:6s} ({yahoo}) {len(bajadas[local][1])} ruedas")
        except Exception as e:
            errores[local] = f"{yahoo}: {e}"
            print(f"ERR {local:6s} ({yahoo}) {e}", file=sys.stderr)
        time.sleep(0.4)
    if "SPY" not in bajadas:
        raise SystemExit("No pude bajar SPY: sin calendario base, no escribo nada.")
    dates = sorted(bajadas["SPY"][1].keys())
    series = {}
    for local, (yahoo, s) in bajadas.items():
        series[local] = {"y": yahoo, "p": [redondear(s[d]) if d in s else None for d in dates]}
    data = {
        "updated": datetime.date.today().isoformat(),
        "fuente": "Yahoo Finance, cierre ajustado (dividendos + splits), USD",
        "dates": dates,
        "series": series,
        "errores": errores,
    }
    with open("data/precios.json", "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"OK · {len(series)} series · {len(dates)} ruedas · {len(errores)} errores")


if __name__ == "__main__":
    main()
