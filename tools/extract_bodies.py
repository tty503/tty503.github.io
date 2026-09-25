#!/usr/bin/env python3
"""Extrae el cuerpo de los artículos desde el historial git y lo normaliza al
markup del design system v4.

Por qué existe: el commit 5a34233 condensó los 33 artículos a resúmenes de
~270 palabras (8.966 palabras en total). Las versiones largas siguen en el
historial: 142.273 palabras. Este script las recupera y las deja en el
subconjunto de markup que el CSS actual sabe renderizar.

Uso:
    python3 tools/extract_bodies.py <commit>            # extrae los cuerpos
    python3 tools/extract_bodies.py --report             # inventario de palabras
"""
import html as H
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path("/tmp/tty503-cuerpo")

# Clases del diseño terminal viejo que no existen en style.css v4. Se eliminan
# o se mapean a una equivalente actual.
DROP_CLASSES = {
    "mono", "text", "text-muted", "line-accent", "badge-text",
    "toc-title", "toc-toggle", "comment", "node", "reg", "val",
}
CLASS_MAP = {
    "section-title mono": "",       # -> <h2> pelado
    "verdict-content mono": "",
    "verdict-badge high mono": "badge",
    "verdict-badge med mono": "badge",
    "image-caption mono": "caption",
}


def strip_svg_blocks(s):
    """Los diagramas SVG del diseño viejo incompaten con el ancho del layout y
    arrastran estilos inline. Se conserva el <figcaption> si lo hay."""
    s = re.sub(r"<svg.*?</svg>", "", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<path[^>]*/?>", "", s)
    s = re.sub(r"<rect[^>]*/?>", "", s)
    s = re.sub(r"<text.*?</text>", "", s, flags=re.S)
    return s


def _balanced_divs(s, classname):
    """Sustituye <div class="classname ...">...</div> equilibrando la anidación
    de <div>. Un regex no puede hacerlo: los bloques de código y las tablas del
    diseño viejo contienen divs internos, y un cierre-por-ocurrencia deja
    <pre> sin abrir."""
    out, i = [], 0
    pat = re.compile(rf'<div class="{classname}[^"]*">')
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:])
            break
        out.append(s[i:m.start()])
        depth, j = 1, m.end()
        while depth and j < len(s):
            nxt_open = s.find("<div", j)
            nxt_close = s.find("</div>", j)
            if nxt_close == -1:
                j = len(s)
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                j = nxt_open + 4
            else:
                depth -= 1
                j = nxt_close + 6
        inner = s[m.end():j - 6] if depth == 0 else s[m.end():]
        out.append(_TRANSFORM.get(classname, lambda x: x)(inner))
        i = j
    return "".join(out)


def _code_block(inner):
    # quita el header de lenguaje si lo hubiera
    inner = re.sub(r'^\s*<div class="code-?header[^"]*">.*?</div>\s*', "", inner, flags=re.S)
    return "<pre><code>" + inner.strip() + "</code></pre>"


def _table(inner):
    if "<table" not in inner:
        return inner
    t = re.search(r"<table.*?</table>", inner, flags=re.S)
    return '<div class="table-wrap">' + t.group(0) + "</div>"


def _figure(inner):
    img = re.search(r"<img[^>]*>", inner)
    if not img:
        return inner
    cap = re.search(r'<span class="caption">(.*?)</span>', inner, flags=re.S)
    out = "<figure>" + img.group(0)
    if cap:
        out += "<figcaption>" + cap.group(1) + "</figcaption>"
    return out + "</figure>"


def _callout(inner):
    t = re.search(r'<div class="callout-title[^"]*">(.*?)</div>', inner, flags=re.S)
    body = re.sub(r'<div class="callout-title[^"]*">.*?</div>', "", inner, flags=re.S)
    body = re.sub(r"^\s*<[^>]+>\s*", "", body.strip())
    out = "<blockquote>"
    if t:
        out += "<p><strong>" + t.group(1) + "</strong></p>"
    return out + body + "</blockquote>"


def _verdict(inner):
    body = re.sub(r'<span class="badge">.*?</span>', "", inner, flags=re.S)
    body = re.sub(r"</?div[^>]*>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return '<p class="veredicto">' + body + "</p>"


_TRANSFORM = {
    "code-block": _code_block,
    "table-wrapper": _table,
    "image-container": _figure,
    "callout": _callout,
    "callout-warning": _callout,
    "verdict-box": _verdict,
}


def drop_element(s, tag):
    """Elimina un elemento y su contenido (details de TOC, scripts)."""
    s = re.sub(rf"<{tag}\b.*?</{tag}>", "", s, flags=re.S)
    return re.sub(rf"<{tag}\b[^>]*/?>", "", s)


def clean_classes(s):
    def fix(m):
        raw = m.group(1)
        keep = [c for c in raw.split() if c not in DROP_CLASSES]
        keep = [CLASS_MAP.get(c, c) for c in keep]
        keep = [c for c in keep if c]
        if not keep:
            return ""
        return ' class="' + " ".join(keep) + '"'
    s = re.sub(r' class="([^"]*)"', fix, s)
    return re.sub(r"\s+>", ">", s)


def balance_p(s):
    """El diseño viejo relied on implicit <p> closes: sobran </p> sueltos.
    Recorre el flujo y elimina los cierres sin apertura previa."""
    out, depth, i = [], 0, 0
    for m in re.finditer(r"<p[^>]*>|</p>", s):
        out.append(s[i:m.start()])
        if m.group(0) == "</p>":
            if depth == 0:
                i = m.end()
                continue
            depth -= 1
        else:
            depth += 1
        out.append(m.group(0))
        i = m.end()
    out.append(s[i:])
    return "".join(out) + "</p>" * depth


def normalize(s):
    s = drop_element(s, "script")
    s = drop_element(s, "details")          # el TOC viejo no aplica
    s = strip_svg_blocks(s)
    # bloques con anidacion: se resuelven ANTES de limpiar clases, porque el
    # matcher necesita la clase original para localizar el bloque.
    for cls in ("code-block", "table-wrapper", "image-container",
                "callout-warning", "callout", "verdict-box"):
        s = _balanced_divs(s, cls)
    s = clean_classes(s)
    s = re.sub(r'<h2[^>]*id="c\d+"[^>]*>', "<h2>", s)
    s = re.sub(r"<h2[^>]*>", "<h2>", s)
    s = re.sub(r"<h3[^>]*>", "<h3>", s)
    s = re.sub(r"</?span[^>]*>", "", s)     # el heading llevaba el numero en span
    s = re.sub(r'\sstyle="[^"]*"', "", s)
    s = re.sub(r"</?div[^>]*>", "", s)      # restos de contenedores
    s = balance_p(s)
    return s


def body_of(raw_html):
    """Aísla el cuerpo: dentro de <article>, saltando el <header>."""
    a = raw_html.find('<article')
    if a == -1:
        return ""
    hdr = raw_html.find("<header", a)
    end_hdr = raw_html.find("</header>", hdr) if hdr != -1 else -1
    start = end_hdr + len("</header>") if end_hdr != -1 else a
    end = raw_html.find("</article>", start)
    return raw_html[start:end] if end != -1 else raw_html[start:]


def main():
    if "--report" in sys.argv:
        return
    commit = sys.argv[1]
    import subprocess
    OUT.mkdir(parents=True, exist_ok=True)
    files = subprocess.run(
        ["git", "ls-tree", "--name-only", commit],
        capture_output=True, text=True, cwd=ROOT).stdout.split()
    n = 0
    for f in files:
        if not f.endswith(".html") or f in (
                "index.html", "404.html", "aboutme.html", "art-001.html"):
            continue
        raw = subprocess.run(["git", "show", f"{commit}:{f}"],
                             capture_output=True, text=True, cwd=ROOT).stdout
        b = body_of(raw)
        if not b.strip():
            continue
        slug = f[:-5]
        clean = normalize(b)
        clean = re.sub(r"\n\s*\n+", "\n", clean).strip()
        (OUT / f"{slug}.html").write_text(clean, encoding="utf-8")
        w = len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", clean)))
        print(f"{w:>6} palabras  {slug}")
        n += 1
    print(f"\n{n} cuerpos extraídos de {commit} -> {OUT}")


if __name__ == "__main__":
    main()
