# scripts/routes_probe.py
from app import create_app
a = create_app()
for r in sorted(a.url_map.iter_rules(), key=lambda x: x.rule):
    print(f"{','.join(sorted(r.methods))} {r.rule}")