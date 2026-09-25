#!/usr/bin/env python3
"""Generador del sitio tty503.com — ensambla chrome + meta + cuerpo por página.

Design system v4: minimalista, blanco/negro, degradados suaves, sin emojis,
lenguaje simple, SEO completo (canonical, OG, Twitter, JSON-LD, sitemap, RSS).
"""
import json
import html
import datetime
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SITE = ROOT.parent           # raíz del repo (GitHub Pages)
META = json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))
BASE = META["site"]["url"].rstrip("/")

HEAD = """
<link rel="stylesheet" href="assets/css/style.css">
<link rel="alternate" type="application/rss+xml" title="tty503 — blog" href="https://tty503.com/feed.xml">
"""


def favicon():
    return """<link rel="icon" type="image/png" href="hat.png">
<link rel="apple-touch-icon" href="hat.png">
<meta name="theme-color" content="#ffffff">
<meta name="color-scheme" content="light">"""


def gtag():
    g = META["site"]["ga"]
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>\n'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js',new Date());gtag('config','{g}');</script>")


def head(title, desc, canonical, ogtype="article", published=None, modified=None):
    img = f"{BASE}/p1.jpg"
    kw = ("tty503, Christian Márquez, seguridad informática, threat intelligence, "
          "ingeniería inversa, malware analysis, vulnerability research, seguridad OT, "
          "agentes de IA locales, automatización, blog técnico")
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


def nav():
    brand = '<a class="brand" href="index.html"><span class="dot"></span>tty503</a>'
    links = ('<nav class="nav-links">'
             '<a href="index.html">Inicio</a>'
             '<a href="index.html#escritos">Escritos</a>'
             '<a href="aboutme.html">Sobre mí</a>'
             '<a class="cta" href="https://github.com/tty503" target="_blank" rel="noopener">GitHub</a>'
             '</nav>')
    toggle = '<button class="nav-toggle" aria-label="Abrir menú">Menú</button>'
    return f'<nav class="site-nav"><div class="nav-inner">{brand}{links}{toggle}</div></nav>'


def footer():
    social = "".join(
        f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>'
        for name, url in META["social"]
    )
    note = ("© <span data-year></span> Christian Márquez (tty503). Investigación en seguridad y "
            "herramientas propias, documentadas con honestidad. Los detalles explotables de los "
            "hallazgos se omiten por política de divulgación responsable.")
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
    arr = [{"@type": "ListItem", "position": 1,
            "item": {"@id": f"{BASE}/index.html", "name": "tty503"}}]
    if data.get("series"):
        arr.append({"@type": "ListItem", "position": 2,
                    "item": {"@id": f"{BASE}/{data['series']}.html", "name": "Serie"}})
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


def read_min(body_html):
    """Tiempo de lectura REAL derivado del cuerpo (200 palabras/min).

    Antes se usaba el campo 'read' de meta.json, escrito a mano: declaraba
    '18 min' y '120 min' sobre posts de 299 y 225 palabras. Era un dato falso
    publicado en el HTML de todas las páginas. Ahora se calcula.
    """
    plain = re.sub(r"<[^>]+>", " ", body_html)
    words = len(re.findall(r"\b\w+\b", plain, re.UNICODE))
    return max(1, round(words / 200))


def build_post(slug, data):
    body = (ROOT / "posts" / f"{slug}.html").read_text(encoding="utf-8")
    canon = f"{BASE}/{slug}.html"
    crumb = [("index.html", "tty503")]
    if data.get("series"):
        crumb.append((f"{data['series']}.html", "Serie"))
    crumb.append((f"{slug}.html", data["title"][:44]))
    tags = "".join(f'<span class="chip">{html.escape(t)}</span>' for t in data["tags"])
    meta_span = (f'<span>{data["date"]}</span>'
                 f'<span>{read_min(body)} min</span>'
                 f'<span>{data["cat"]}</span>')
    related = data.get("related", [])
    rel_html = ""
    if related:
        cards = []
        for rslug in related:
            rdata = META["pages"].get(rslug)
            if not rdata:
                continue
            cards.append(
                f'<div class="post-item"><span class="meta">{rdata["date"]} · {rdata["cat"]}</span>'
                f'<a href="{rslug}.html">{html.escape(rdata["title"])}</a></div>')
        rel_html = (f'<section class="related"><h2>Sigue leyendo</h2>'
                    f'<div class="grid-2">{"".join(cards)}</div></section>')
    return f"""{head(data["title"], data["desc"], canon, published=data.get("date"), modified=data.get("date"))}
<body>
{nav()}
<main class="post container">
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


def writings_html():
    items = []
    pages = sorted(META["pages"].items(), key=lambda kv: kv[1].get("date", ""), reverse=True)
    for slug, p in pages:
        badge = f'<span class="badge">{html.escape(p["badge"])}</span>' if p.get("badge") else ""
        mins = read_min((ROOT / "posts" / f"{slug}.html").read_text(encoding="utf-8"))
        items.append(
            f'<li><a href="{slug}.html">'
            f'<div class="meta"><span class="cat">{html.escape(p["cat"])}</span> · {p["date"]} · {mins} min</div>'
            f'<div class="t">{html.escape(p["title"])}</div>'
            f'<div class="d">{html.escape(p["desc"])}</div>'
            f'{badge}</a></li>')
    return '<ul class="posts">' + "".join(items) + "</ul>"


def build_index():
    body = (ROOT / "pages" / "index.html").read_text(encoding="utf-8")
    if "{{WRITINGS}}" in body:
        body = body.replace("{{WRITINGS}}", writings_html())
    title = "tty503 — Christian Márquez, investigación en seguridad y agentes de IA locales"
    desc = ("Christian Márquez (tty503): investigación en seguridad informática, "
            "ingeniería inversa y agentes de IA locales. Documento trabajo verificado, "
            "con divulgación responsable, desde Venezuela.")
    canon = f"{BASE}/"
    jl = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Person",
      "@id": "https://tty503.com/#person",
      "name": "Christian Márquez",
      "alternateName": ["tty503", "Christian Marquez"],
      "url": "https://tty503.com",
      "image": "https://tty503.com/p1.jpg",
      "sameAs": ["https://github.com/tty503", "https://linkedin.com/in/tty503", "https://x.com/tty_503"],
      "jobTitle": "Investigador en seguridad informática",
      "description": "Investiga y documenta seguridad de software, ingeniería inversa, análisis de malware y el trabajo con agentes de IA locales."
    },
    {
      "@type": "WebSite",
      "@id": "https://tty503.com/#website",
      "url": "https://tty503.com",
      "name": "tty503",
      "inLanguage": "es",
      "publisher": { "@id": "https://tty503.com/#person" }
    }
  ]
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


def build_generic(slug, body_path, title, desc, jsonld_type="WebPage", noindex=False):
    body = (ROOT / body_path).read_text(encoding="utf-8")
    canon = f"{BASE}/{slug}"
    _head = head(title, desc, canon, ogtype="website")
    robots = '<meta name="robots" content="noindex, follow">' if noindex else ""
    _head = _head.replace(
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">',
        robots or '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">')
    jl = (f'<script type="application/ld+json">'
          f'{{"@context":"https://schema.org","@type":"{jsonld_type}","name":{json.dumps(title)},'
          f'"url":"{canon}","author":{{"@type":"Person","name":"Christian Márquez"}}}}'
          f'</script>')
    return f"""{_head}
<body>
{nav()}
{body}
{footer()}
{jl}
</body>
</html>"""


def build_sitemap():
    urls = [f"{BASE}/", f"{BASE}/aboutme.html"]
    for slug in META["pages"]:
        urls.append(f"{BASE}/{slug}.html")
    last = META["site"]["time"][:10]
    items = "".join(
        f"  <url><loc>{u}</loc><lastmod>{last}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>0.8</priority></url>\n"
        for u in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}</urlset>
"""


def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
"""


def build_feed():
    items = []
    now = META["site"]["time"].replace("T00:00:00Z", "")
    for slug, data in META["pages"].items():
        pub = data["date"]
        try:
            pub_rfc = datetime.datetime.strptime(pub, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        except ValueError:
            pub_rfc = f"{now} 00:00:00 +0000"
        body = (ROOT / "posts" / f"{slug}.html").read_text(encoding="utf-8")
        body_txt = html.escape(re.sub(r"<[^>]+>", " ", body))[:500].strip() + "…"
        items.append(f"""    <item>
      <title>{html.escape(data['title'])}</title>
      <link>{BASE}/{slug}.html</link>
      <guid isPermaLink="true">{BASE}/{slug}.html</guid>
      <pubDate>{pub_rfc}</pubDate>
      <description>{body_txt}</description>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>tty503 — blog</title>
  <link>{BASE}/</link>
  <description>Investigación en seguridad informática, ingeniería inversa y agentes de IA locales.</description>
  <language>es</language>
  <lastBuildDate>{now} 00:00:00 +0000</lastBuildDate>
  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
</channel>
</rss>
"""
    return rss


def main():
    for slug, data in META["pages"].items():
        out = build_post(slug, data)
        (SITE / f"{slug}.html").write_text(out, encoding="utf-8")
        print("ok", slug, f"{len(out)//1024} KB")
    (SITE / "index.html").write_text(build_index(), encoding="utf-8")
    print("ok index.html")
    (SITE / "aboutme.html").write_text(
        build_generic("aboutme.html", "pages/about.html",
                      "Sobre mí — Christian Márquez (tty503)",
                      "Christian Márquez (tty503): investigador en seguridad informática autodidacta. "
                      "Ingeniería inversa, análisis de malware, investigación de vulnerabilidades y "
                      "agentes de IA locales, documentados desde Venezuela.",
                      jsonld_type="ProfilePage"), encoding="utf-8")
    print("ok aboutme.html")
    (SITE / "404.html").write_text(
        build_generic("404.html", "pages/404.html",
                      "404 — Página no encontrada | tty503",
                      "La ruta solicitada no existe. Volver al sitio de Christian Márquez (tty503).",
                      noindex=True), encoding="utf-8")
    print("ok 404.html")
    (SITE / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (SITE / "robots.txt").write_text(build_robots(), encoding="utf-8")
    (SITE / "feed.xml").write_text(build_feed(), encoding="utf-8")
    print("ok sitemap.xml + robots.txt + feed.xml")


if __name__ == "__main__":
    main()