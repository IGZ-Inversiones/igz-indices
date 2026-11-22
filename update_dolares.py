#!/usr/bin/env python3
"""Genera data/dolares.json: MEP (bolsa) y CCL diarios para dolarizar carteras.
Fuente: api.argentinadatos.com (cotización de venta).
Formato: {"updated": "...", "fuente": "...", "mep": [[fecha, venta], ...], "ccl": [[fecha, venta], ...]}
"""
import json, urllib.request, datetime, os

UA = {"User-Agent": "Mozilla/5.0 (compatible; IGZ-dolares/1.0)"}
BASE = "https://api.argentinadatos.com/v1/cotizaciones/dolares/"

def bajar(casa):
    req = urllib.request.Request(BASE + casa, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    out = {}
    for x in d:
        v = x.get("venta") or x.get("compra")
        if v:
            out[x["fecha"][:10]] = float(v)
    return [[k, out[k]] for k in sorted(out)]

def main():
    os.makedirs("data", exist_ok=True)
    data = {"updated": datetime.date.today().isoformat(),
            "fuente": "api.argentinadatos.com, cotización de venta",
            "mep": bajar("bolsa"), "ccl": bajar("contadoconliqui")}
    with open("data/dolares.json", "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("OK · MEP", len(data["mep"]), "· CCL", len(data["ccl"]))

if __name__ == "__main__":
    main()
