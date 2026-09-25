#!/usr/bin/env python3
"""Reescribe src/meta.json a partir de la taxonomia de 12 pilares.

Genera tambien el mapa de redireccion: cada slug absorbido o retirado apunta a
el pillar que lo contiene. GitHub Pages no sirve 301 (es contenido estatico sin
mod_rewrite), asi que el redireccionado se hace con stubs HTML: meta refresh
inmediato + canonical al destino + enlace visible de respaldo.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
META = ROOT / "src" / "meta.json"
from assemble_pillars import PILLARS  # la taxonomia es la fuente unica

SPEC = {slug: d for slug, d in PILLARS}

RELATED = {
    "sinks-preauth-daemons-c": ["cazar-con-ia-local", "deteccion-blue-team", "agentes-ia-locales"],
    "cazar-con-ia-local": ["sinks-preauth-daemons-c", "agentes-ia-locales", "analystty"],
    "agentes-ia-locales": ["cazar-con-ia-local", "saint-grail", "sinks-preauth-daemons-c"],
    "exploit-development-y-reversing": ["seguridad-ot-ics", "deteccion-blue-team", "pentest-api-jwt-idor"],
    "seguridad-ot-ics": ["exploit-development-y-reversing", "deteccion-blue-team"],
    "deteccion-blue-team": ["fraude-cripto-y-phishing", "phishing-campanas-y-busqueda", "exploit-development-y-reversing"],
    "fraude-cripto-y-phishing": ["phishing-campanas-y-busqueda", "deteccion-blue-team"],
    "phishing-campanas-y-busqueda": ["fraude-cripto-y-phishing", "laboratorio-de-seguridad"],
    "laboratorio-de-seguridad": ["phishing-campanas-y-busqueda", "cazar-con-ia-local"],
    "saint-grail": ["agentes-ia-locales", "analystty", "cazar-con-ia-local"],
    "analystty": ["saint-grail", "cazar-con-ia-local"],
    "pentest-api-jwt-idor": ["exploit-development-y-reversing", "deteccion-blue-team"],
}

# Cada slug retirado -> pillar destino. Los que no aparecen se fusionan entre si.
REDIRECT = {}
for slug, info in SPEC.items():
    for s in info["sources"]:
        REDIRECT[s] = slug
REDIRECT["divulgacion-responsable"] = "sinks-preauth-daemons-c"

meta = json.loads(META.read_text(encoding="utf-8"))
pages = {}
for slug in SPEC:
    info = SPEC[slug]
    pages[slug] = {
        "title": info["title"],
        "desc": info["desc"],
        "date": info["date"],
        "cat": info["cat"],
        "tags": info["tags"],
        "badge": info["badge"],
        "related": RELATED[slug],
    }
    assert not info.get("read"), "el campo read no se escribe: lo calcula gen.py"

meta["pages"] = pages
meta["site"]["time"] = "2026-09-25T00:00:00Z"
META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"meta.json: {len(pages)} paginas")
print(f"redirecciones: {len(REDIRECT)} slugs -> {len(set(REDIRECT.values()))} destinos")
(ROOT / "meta" / "redirects.json").write_text(
    json.dumps(REDIRECT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
