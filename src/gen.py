#!/usr/bin/env python3
"""Generador del sitio tty503.com — ensambla chrome + meta + cuerpo por página."""
import json, html, os, datetime, hashlib
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT.parent           # raíz del repo (GitHub Pages)
META = json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))
BASE = META["site"]["url"]

HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
"""

def favicon():
    return """<link rel="icon" type="image/png" href="hat.png">
<link rel="apple-touch-icon" href="hat.png">
<meta name="theme-color" content="#08090c">
<meta name="color-scheme" content="dark">"""

def gtag():
    g = META["site"]["ga"]
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{g}');</script>"""

def head(title, desc, canonical, ogtype="article", published=None, modified=None, extra_img=None):
    img = extra_img or f"{BASE}/p1.jpg"
    kw = "tty503, Christian Márquez, threat intelligence, ingeniería inversa, malware analysis, exploit development, seguridad OT, PLC Siemens, vulnerability research, reverse engineering"
    pub = f'<meta property="article:published_time" content="{published}">' if published else ""
    mod = f'<meta property="article:modified_time" content="{modified}">' if modified else ""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
{favicon()}
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="keywords" content="{kw}">
<meta name="author" content="Christian Márquez">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="googlebot" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="tty503">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc[:290])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img}">
<meta property="og:image:alt" content="tty503 — Christian Márquez">
{pub}
{mod}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@tty_503">
<meta name="twitter:creator" content="@tty_503">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc[:190])}">
<meta name="twitter:image" content="{img}">
{gtag()}
{HEAD}
</head>"""

def nav(back=None):
    brand = """<a class="brand" href="index.html"><span class="dot"></span>tty503<span class="sub">/ &nbsp;</span></a>"""
    links = ('<nav class="nav-links">'
             '<a href="index.html">Inicio</a>'
             '<a href="index.html#research">Investigaciones</a>'
             '<a href="index.html#publications">Publicaciones</a>'
             '<a href="aboutme.html">Sobre mí</a>'
             '<a class="cta" href="https://github.com/tty503" target="_blank" rel="noopener">GitHub</a>'
             '</nav>')
    toggle = '<button class="nav-toggle" aria-label="Menú">☰</button>'
    return f'<div class="bg-fx"></div>\n<nav class="site-nav"><div class="nav-inner">{brand}{links}{toggle}</div></nav>'

def footer(extra=""):
    social = "".join(
        f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>'
        for name, url in META["social"]
    )
    note = ("© <span data-year></span> Christian Márquez · Threat Intelligence · Ingeniería Inversa · "
            "Exploit Development · Seguridad OT. Venezuela.")
    return f"""<footer class="site-footer"><div class="footer-inner">
<div class="social">{social}</div>
<p class="footer-note">{note}</p>
</div></footer>
<button class="to-top" aria-label="Volver arriba">↑</button>
<script src="assets/js/main.js"></script>"""

def breadcrumb(crumb_links):
    parts = "".join(f'<a href="{u}">{t}</a><span class="sep">/</span>' for u, t in crumb_links)
    return f'<nav class="breadcrumb">{parts}</nav>'

def article_jsonld(data, canonical):
    series = data.get("series")
    arr = [{
        "@type": "ListItem",
        "position": 1,
        "item": {"@id": f"{BASE}/index.html", "name": "tty503"}
    }]
    if series:
        arr.append({"@type": "ListItem", "position": 2,
                    "item": {"@id": f"{BASE}/{series}.html", "name": "Serie"}})
    arr.append({"@type": "ListItem", "position": len(arr) + 1,
                "item": {"@id": canonical, "name": data["title"]}})
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Article",
      "headline": {json.dumps(data["title"])},
      "description": {json.dumps(data["desc"])},
      "author": {{ "@type": "Person", "name": "Christian Márquez", "url": "{BASE}" }},
      "publisher": {{ "@type": "Organization", "name": "tty503" }},
      "datePublished": {json.dumps(data["date"])},
      "dateModified": {json.dumps(data["date"])},
      "mainEntityOfPage": {json.dumps(canonical)},
      "inLanguage": "es",
      "keywords": {json.dumps(", ".join(data["tags"]))}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": {json.dumps(arr, ensure_ascii=False)}
    }}
  ]
}}
</script>"""

def page_open(data, canonical, kind="article"):
    ogtype = "article" if kind == "article" else "website"
    return head(data["title"], data["desc"], canonical, ogtype=ogtype,
                published=data.get("date"), modified=data.get("date"))

def build_post(slug, data):
    body = (ROOT / "posts" / f"{slug}.html").read_text(encoding="utf-8")
    canon = f"{BASE}/{slug}.html"
    crumb = [("index.html", "tty503")]
    if data.get("series"):
        crumb.append((f"{data['series']}.html", "Serie"))
    crumb.append((f"{slug}.html", data["title"][:48]))
    tags = "".join(f'<span class="chip">{html.escape(t)}</span>' for t in data["tags"])
    read = data["read"]
    meta_span = f'<span>📅 {data["date"]}</span><span>⏱ {read}</span><span>🏷 {data["cat"]}</span>'
    related = data.get("related", [])
    rel_html = ""
    if related:
        cards = []
        for rslug in related:
            rdata = META["pages"].get(rslug)
            if not rdata:
                continue
            badge = f'<span class="badge badge-{rdata["badge"]}">{rdata["cat"]}</span>'
            cards.append(
                f'<a class="card" href="{rslug}.html"><span class="arrow">→</span>'
                f'<div class="meta"><span>{rdata["date"]}</span><span>{rdata["read"]}</span></div>'
                f'<div class="t">{html.escape(rdata["title"])}</div>'
                f'<div class="d">{html.escape(rdata["desc"][:120])}</div>{badge}</a>')
        rel_html = f'<section class="related"><h2>Sigue leyendo</h2><div class="grid grid-2">{"".join(cards)}</div></section>'
    return f"""{page_open(data, canon)}
<body>
{nav()}
<main class="post">
{breadcrumb(crumb)}
<header class="post-head">
  <div class="post-tags">{tags}</div>
  <h1>{html.escape(data["title"])}</h1>
  <p class="lede">{html.escape(data["desc"])}</p>
  <div class="post-meta">{meta_span}</div>
</header>
<article class="post-body">
{body}
</article>
{rel_html}
</main>
{footer()}
{article_jsonld(data, canon)}
</body>
</html>"""

def build_generic(slug, body_path, title, desc, jsonld_type="WebPage", extra_body=None, noindex=False):
    body = (ROOT / body_path).read_text(encoding="utf-8")
    canon = f"{BASE}/{slug}"
    _head = head(title, desc, canon, ogtype="website")
    robots = '<meta name="robots" content="noindex, follow">' if noindex else ""
    _head = _head.replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', robots or '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">')
    jl = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"{jsonld_type}","name":{json.dumps(title)},"url":"{canon}","author":{{"@type":"Person","name":"Christian Márquez"}}}}
</script>"""
    return f"""{_head}
<body>
{nav()}
{body}
{footer()}
{jl}
</body>
</html>"""

def build_index():
    body = (ROOT / "pages" / "index.html").read_text(encoding="utf-8")
    title = "Christian Márquez (tty503) — Threat Intelligence, Reversing y Exploit Development"
    desc = ("Christian Márquez (tty503): especialista en threat intelligence, ingeniería inversa de malware, "
            "exploit development y seguridad OT/PLC. Cadenas RCE pre-auth verificadas, análisis de malware a nivel de "
            "bytes y deconstrucción de infraestructuras de fraude financiero, desde Venezuela.")
    canon = f"{BASE}/"
    jl = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://tty503.com/#person",
  "name": "Christian Márquez",
  "alternateName": ["tty503", "Christian Marquez"],
  "url": "https://tty503.com",
  "image": "https://tty503.com/p1.jpg",
  "sameAs": ["https://github.com/tty503", "https://linkedin.com/in/tty503", "https://x.com/tty_503"],
  "jobTitle": "Threat Intelligence Specialist · Reverse Engineer · Exploit Developer · OT Security Researcher",
  "worksFor": { "@type": "Organization", "name": "tty503 Independent Consultant" },
  "knowsAbout": [
    "Threat Intelligence", "Malware Analysis", "Reverse Engineering", "Exploit Development",
    "Binary Exploitation", "ROP", "Shellcode", "Assembly x86/x64", "ARM64", "Windows Internals",
    "PLC Siemens S5/S7", "SCADA Security", "OT Security", "Critical Infrastructure", "CVE Research",
    "DevSecOps", "Ansible", "Terraform", "Proxmox", "Ghidra", "x64dbg", "Capstone", "Wazuh", "SIEM",
    "Honeypot", "Blockchain Forensics", "Pig Butchering", "OSINT", "Python", "Go", "Bash", "Linux",
    "Malware Evasion", "YARA Evasion", "DGA", "MITRE ATT&CK", "Fuzzing", "SAINT GRAIL", "Sherlock"
  ],
  "description": "Especialista en threat intelligence, ingeniería inversa, exploit development y seguridad en infraestructuras críticas OT/PLC. Investiga y documenta cadenas de explotación, malware y fraude financiero desde Venezuela."
}
</script>"""
    return f"""{head(title, desc, canon, ogtype="website")}
<body>
{nav()}
{body}
{footer()}
{jl}
</body>
</html>"""

def build_sitemap():
    urls = [f"{BASE}/", f"{BASE}/aboutme.html"]
    for slug, data in META["pages"].items():
        urls.append(f"{BASE}/{slug}.html")
    items = ""
    for u in urls:
        last = META["site"]["time"]
        items += f"  <url><loc>{u}</loc><lastmod>{last}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}</urlset>
"""

def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
"""

def main():
    for slug, data in META["pages"].items():
        html_out = build_post(slug, data)
        (SITE / f"{slug}.html").write_text(html_out, encoding="utf-8")
        print("ok", slug, f"{len(html_out)//1024} KB", "secciones", data["tags"])
    (SITE / "index.html").write_text(build_index(), encoding="utf-8")
    print("ok index.html")
    adm = META["site"]
    (SITE / "aboutme.html").write_text(
        build_generic("aboutme.html", "pages/about.html",
                      "Christian Márquez (tty503) — Sobre mí | Reversing, Exploit Dev y Seguridad OT",
                      "Ruta completa de Christian Márquez (tty503): de firmware de microcontroladores a threat intelligence, ingeniería inversa, exploit development y seguridad OT/PLC. Trayectoria autodidacta desde 2012 desde Venezuela.",
                      jsonld_type="ProfilePage"), encoding="utf-8")
    print("ok aboutme.html")
    (SITE / "404.html").write_text(
        build_generic("404.html", "pages/404.html",
                      "404 — Página no encontrada | tty503",
                      "Error 404: la ruta solicitada no existe. Volver al portafolio de threat intelligence, ingeniería inversa y seguridad ofensiva de Christian Márquez (tty503).",
                      noindex=True), encoding="utf-8")
    print("ok 404.html")
    (SITE / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (SITE / "robots.txt").write_text(build_robots(), encoding="utf-8")
    print("ok sitemap.xml + robots.txt")

if __name__ == "__main__":
    main()