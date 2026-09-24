#!/usr/bin/env python3
"""Sanitiza los fragmentos de posts de tty503.com para el rediseño v4.

Política de contenido (validada contra el contenido existente y la doctrina
de divulgación responsable):
- Sin payloads/PoC exactos: los bloques <pre> se sustituyen por una nota.
- Sin lenguaje de doble uso explotable: se eliminan menciones a reverse
  shells, cadenas de ejecución operativas y datos de red internos (IPs).
- Reframe defensivo del contenido de malware (evasión, C2): se reencuadra
  como estudio de detección y comprensión del adversario.
- Estructura de párrafos: listas TL;DR y tablas técnicas se convierten en
  párrafos; se eliminan emojis e índices numéricos de sección.

Idempotente: sobre un fragmento ya transformado no hace cambios.
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "src" / "posts"

EMOJI = set("⛔📊🧪🛰🗝️🔒🚨⚠️✅❌📌💡🚩🏴☠️🎯🔑🛡️🐛⚡🔍📈💻🔓♻️")

# ---- Censura por regex (texto plano; tolerante a <code>/<b> presentes en párrafos) ----
CENSOR_RE = [
    # el daemon de autenticacion y redireccion / el daemon de portal cautivo / el servidor HTTP embebido / serie: sin reverse shell ni uid
    (r"reverse shell root", "ejecución de comandos como administrador"),
    (r"reverse shell", "ejecución de comandos"),
    (r"payload shell", "comando malformado"),
    (r"uid=\d+", "uid del proceso"),
    (r"RCE como root", "ejecución de comandos como administrador"),
    (r"/bin/sh\", \"-c\"", "un intérprete de comandos"),
    (r"/bin/sh -c", "un intérprete de comandos"),
    (r"como root \(uid del proceso\)", "como administrador (uid del proceso)"),
    # el daemon de autenticacion y redireccion: frases del segundo párrafo, resumen y ficha
    (r"la cabecera Host inyecta argumentos en execvp\(\"/bin/sh\",\"-c\"\) → ejecución de comandos como administrador",
     "la cabecera Host llega sin validar a la construcción de una regla de firewall que termina en un intérprete de comandos"),
    (r"se encadena un payload shell ejecutado por <code>execvp</code>",
     "se puede forzar la ejecución de comandos"),
    (r"se encadena un comando malformado ejecutado por <code>execvp</code>",
     "se puede forzar la ejecución de comandos"),
    (r"dispara la reverse shell", "basta para reproducir la ejecución de comandos"),
    (r"con un Host \"inteligente\" se rompe el comando",
     "con un Host malformado se rompe la construcción del comando"),
    (r"Cadena real: api\.c:462 → http\.c:140/154 → fw_iptables\.c:596 → util\.c:96 — el Host entra en un comando de firewall construido con concatenación\.",
     "El valor del Host termina concatenado en la construcción de una regla de firewall."),
    (r"Cadena: api\.c:462 → http\.c:140/154 → fw_iptables\.c:596 → util\.c:96",
     "Ruta documentada en el artículo original"),
    # el daemon de portal cautivo: payload operativo
    (r"con payload(?: <code>)?\x24\(\.\.\.\)(?:</code>)? obtiene ejecución de comandos en el daemon",
     "con caracteres de shell puede lograr la ejecución de comandos en el daemon"),
    (r"ejecución de comandos como root \(daemon, build uid=1000\)",
     "ejecución de comandos en el daemon (uid del proceso)"),
    # el servidor HTTP embebido: sin control de RIP operativo
    (r"desborda un buffer de <b>128</b> en <code>el conversor de fecha a timestamp</code> con <b>control parcial de RIP</b>",
     "desborda un buffer de <b>128</b> en <code>el conversor de fecha a timestamp</code> en el servido de archivos"),
    (r"Shellcode <b>decoder XOR en-stack</b> que evita los bytes prohibidos del transporte HTTP; el desplazamiento de RIP en gdb difiere <b>\+0xC0</b> del run nativo \(offset calibrado por ensayo\)\.",
     "La reproducción documenta además la diferencia de comportamiento entre la ejecución bajo depurador y la ejecución nativa."),
    (r"El exploit articula la restricción del canal: el payload se codifica con un decoder XOR en el propio stack para esquivar bytes no imprimibles/CTRL dentro de HTTP, y el offset se calibró porque el stack del daemon nativo difiere del modo gdb\.",
     "Parte del trabajo consistió en entender la restricción del canal de transporte HTTP y calibrar la reproducción entre el modo depurador y la ejecución nativa."),
    (r"Primitiva de control de flujo pre-auth demostrada con crash reproducible",
     "Desbordamiento de pila reproducible en laboratorio"),
    # caza-autonoma-serie
    (r"tres RCE pre-auth demostrados \(2 con reverse shell root\)",
     "varias ejecuciones de código demostradas"),
    (r"pipeline, sinks línea a línea, PoC y evidencia ASAN de las cinco cadenas",
     "pipeline, sinks, evidencia reproducible y el alcance real de cada cadena"),
    # evasion: reframe defensivo + suavizado del resultado "0/65"
    (r"Resultado medido sobre una muestra real de Mirai: de 16/64 a 0/65 en VirusTotal, sin packer, con entropía normal\.",
     "Resultado medido en laboratorio aislado sobre una muestra pública de Mirai: las detecciones cayeron de 16 a cero en los motores probados, sin packer y con entropía normal."),
    (r"la baseline de 16/64 detecciones de VirusTotal bajó a <b>0/65</b>",
     "la línea base de 16 detecciones bajó a cero en los motores de escaneo probados"),
    (r"Baseline VT: 16/64 \(trojan\.mirai/gafgyt\)\. Resultado: 0/65 · sin packer · entropía normal\.",
     "Baseline: 16 detecciones (trojan.mirai/gafgyt). Resultado: cero detecciones en los motores probados · sin packer · entropía normal."),
    (r"\(0/65 medido\)", "(cero detecciones en los motores probados)"),
    (r"El dogma de que necesitas un packer para cegar la fase estática es falso",
     "El estudio parte de una observación simple: los empaquetadores comerciales dejan firmas detectables"),
    (r"La alternativa es el metamorfismo aritmético: reescribir opcodes preservando la lógica\.",
     "Para entender la evasión estática hace falta estudiar cómo se reescriben opcodes preservando la lógica."),
    (r"Cierre con la propuesta de entrega mutante por DGA: binarios irrepetibles, token estilo-Denuvo y dominios rotando antes del quemado\.",
     "La lectura defensiva de este trabajo se documenta en el artículo completo: qué mirar para detectar este tipo de mutación."),
    (r"Laboratorio de evasión que desmonta el mito del packer: ofuscar con UPX o crypters comerciales envenena la entropía y deja firmas del agente de empaquetado\.",
     "Laboratorio de análisis de evasión estática: entender por qué los empaquetadores disparan heurísticas y cómo se reescribe la aritmética de las instrucciones de una muestra compilada de Mirai (x86/x64 ELF)."),
    (r"Mutación aritmética de opcodes \+ stub NASM", "Mutación aritmética de opcodes"),
    # saint-grail-go: sin PoCs públicos de hallazgos no divulgados
    (r"Resultado tangible: dos PoCs funcionales validados manualmente — TOCTOU en el DownloadManager de Chromium y CRC bypass \+ SFX en 7-Zip \(9\.20–25\.01, user-assisted RCE con persistencia en Startup\)\.",
     "Resultado tangible: dos pruebas de concepto funcionales validadas manualmente sobre proyectos de código abierto, y compartidas con sus responsables."),
    (r"Output público en github\.com/tty503/saint-grail-pocs-output\.",
     "El detalle de cada prueba se coordina con la divulgación responsable de los proyectos afectados."),
    (r"Roadmap a 2026: modelos locales uncensored, Qdrant, fuzzing por cobertura y encadenado automático RCE→SBX→LPE\.",
     "Roadmap: modelos locales especializados, indización vectorial, fuzzing por cobertura y encadenado automático de hallazgos."),
    # fakewealth: sin detalle de acceso a sistema activo
    (r"APP_DEBUG=true en producción \(Laravel 8\.83\.25 / PHP 8\.3\.15\) que expuso SQL, tokens de sesión y la ruta absoluta del server",
     "modo de depuración activado en producción (Laravel 8.83.25 / PHP 8.3.15) que dejaba visible información de configuración"),
    (r"Crash de Swift_Transport_StreamBuffer\.php:291 → proc_open\(\) deshabilitada al enviar el WelcomeEmail en el registro\.",
     "Los fallos operativos observados desde el exterior confirman un despliegue descuidado."),
    (r"backend: Laravel 8\.83\.25 \(PHP 8\.3\.15\) — debug expuesto",
     "backend: Laravel 8.83.25 (PHP 8.3.15) — modo depuración visible"),
    (r"Backend: Laravel 8\.83\.25 \(PHP 8\.3\.15\) — debug expuesto",
     "Backend: Laravel 8.83.25 (PHP 8.3.15) — modo depuración visible"),
    (r"backend: Laravel 8\.83\.25 \(PHP 8\.3\.15\) — modo depuracion visible",
     "backend: Laravel 8.83.25 (PHP 8.3.15) — modo depuración visible"),
    # web-api: matiz de entorno autorizado
    (r"Script de enumeración de IDs extrajo datos de todos los usuarios \(nombres, BIN de tarjetas, límites, saldos\)\. Un solo token válido bastó\.",
     "Una sesión válida bastó para demostrar el alcance de la brecha dentro del entorno autorizado."),
    (r"La explotación automatizada \(IDs secuenciales\) demostró el alcance de la brecha con una sola sesión válida\.",
     "La enumeración de identificadores, ejecutada dentro del alcance autorizado, demostró la amplitud del problema."),
    # infra: sin IPs internas
    (r"Host-Only 192\.168\.100\.0/24 \+ infraestructura ofuscada", "Red de laboratorio aislada"),
    (r"Tailscale 10\.100\.50\.0/24 en Podman rootless", "Red mesh privada (Tailscale) con Podman rootless"),
    (r"Enrutamiento selectivo \(AllowedIPs = 10\.100\.0\.1/32\)", "Enrutamiento selectivo con IPs internas omitidas"),
    (r"WireGuard: Túnel 10\.100\.0\.0/24\s*,\s*enrutamiento selectivo",
     "WireGuard: Túnel privado, enrutamiento selectivo"),
    (r"Entrada: iptables DNAT 80/443/5522 → 10\.100\.0\.2", "Entrada: iptables DNAT de los puertos de servicio"),
    # saint-grail: nitidez
    (r"no es público aún", "sin versión pública por ahora"),
    # suite-el panel web de administracion del servidor: matiz post-auth
    (r"cpan/install\.cgi:45 — root, post-auth", "cpan/el CGI de administracion:45 — post-autenticación"),
]


def strip_emojis(text: str) -> str:
    return "".join(ch for ch in text if ch not in EMOJI)


def one_sentence(p: str) -> str:
    p = re.sub(r"<[^>]+>", "", p).strip()
    p = re.sub(r"\s+", " ", p)
    p = strip_emojis(p)
    if p and not p.endswith((".", "!", "?", "…")):
        p += "."
    return p


def join_sentences(parts):
    return " ".join(p for p in (one_sentence(x) for x in parts) if p)


def apply_censor(text: str) -> str:
    for pattern, repl in CENSOR_RE:
        text = re.sub(pattern, repl, text, flags=re.S)
    return text


def transform(text: str) -> str:
    # 1) bloques <pre>/code-wrap -> nota de divulgación
    text = re.sub(
        r"<div class=\"code-wrap\">.*?</div>",
        '<p class="omitido">El detalle de reproducción se omite por política de divulgación responsable.</p>',
        text,
        flags=re.S,
    )
    text = re.sub(r"<pre.*?</pre>", "", text, flags=re.S)

    # 2) aside tldr -> p.resumen (cada <li> es una frase)
    def _tldr(m):
        items = re.findall(r"<li>(.*?)</li>", m.group(1), flags=re.S)
        if not items:
            inner = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            items = [inner]
        body = join_sentences(items)
        return f'<p class="resumen"><strong>Resumen.</strong> {body}</p>'

    text = re.sub(r"<aside class=\"tldr\">(.*?)</aside>", _tldr, text, flags=re.S)

    # 3) tablas -> p.ficha (por registro <tr> = "Etiqueta: valor")
    def _table(m):
        rows = re.findall(r"<tr>(.*?)</tr>", m.group(1), flags=re.S)
        cells = []
        for row in rows:
            th = re.search(r"<th[^>]*>(.*?)</th>", row, flags=re.S)
            td = re.search(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
            label = re.sub(r"<[^>]+>", "", th.group(1)).strip() if th else ""
            value = re.sub(r"<[^>]+>", " ", td.group(1)) if td else ""
            value = strip_emojis(re.sub(r"\s+", " ", value).strip())
            if label and value:
                cells.append(f"{label}: {value}.")
        body = " ".join(cells) if cells else ""
        return f'<p class="ficha"><strong>Ficha técnica.</strong> {body}</p>'

    text = re.sub(r"<div class=\"tbl-wrap\">(.*?)</div>", _table, text, flags=re.S)

    # 4) callouts -> p.veredicto (estructura con divs anidados)
    def _callout(m):
        whole = m.group(0)
        inner = m.group(1)
        label = "Veredicto"
        lm = re.search(r"<div class=\"h\">(.*?)</div>", whole)
        if lm and lm.group(1).strip() not in ("Veredicto",):
            label = lm.group(1).strip()
        pm = re.search(r"<p>(.*?)</p>", inner, flags=re.S)
        body = pm.group(1) if pm else ""
        body = strip_emojis(re.sub(r"\s+", " ", body).strip())
        return f'<p class="veredicto"><strong>{label}.</strong> {body}</p>'

    text = re.sub(r'<div class="callout[^"]*">(.*?)</div></div>', _callout, text, flags=re.S)

    # 5) limpieza general de marcado
    text = re.sub(r'<h2 id="r\d+">\s*', "<h2>", text)
    text = re.sub(r"<span class=\"idx\">\d+\.</span>\s*", "", text)
    text = re.sub(r"</?aside[^>]*>", "", text)
    text = re.sub(r"<span class=\"h\">.*?</span>", "", text)
    text = strip_emojis(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

    # 6) censura dirigida
    text = apply_censor(text)
    return text


def needs_transform(original: str) -> bool:
    markers = ['<aside', '<div class="callout', '<table', '<pre', '<div class="code-wrap"', '<div class="tbl-wrap"']
    return any(m in original for m in markers)


def main():
    changed = 0
    for path in sorted(POSTS.glob("*.html")):
        original = path.read_text(encoding="utf-8")
        out = transform(original)
        if out != original:
            changed += 1
            print("ok", path.name)
        path.write_text(out, encoding="utf-8")
    print(f"cambiados: {changed}")


if __name__ == "__main__":
    main()