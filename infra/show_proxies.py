"""Print Toxiproxy proxies and their toxics. Usage: python3 infra/show_proxies.py [api_url]"""
import json
import sys
import urllib.request

api = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8474"
with urllib.request.urlopen(f"{api}/proxies", timeout=5) as resp:
    proxies = json.load(resp)

for name, p in sorted(proxies.items()):
    toxics = ", ".join(f"{t['name']}({t['type']})" for t in p["toxics"]) or "none"
    print(f"  {name:<10} {p['listen']:<14} -> {p['upstream']:<16} enabled={p['enabled']}  toxics: {toxics}")
