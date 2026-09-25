#!/usr/bin/env python3
"""Ensambla los 12 pilares a partir de los cuerpos recuperados del historial.

El commit 5a34273 condenso los 33 articulos a ~270 palabras cada uno. Este
script reconstruye cada pillar concatenando las versiones largas que siguen
vivas en el historial (75.215 palabras en total), renumerando las secciones
para que el conjunto se lea como un solo articulo y no como un pegado.

P1 pasa ademas por tools/dename.py, que sustituye los nombres de producto por
descripciones funcionales. Los demas pilares no se desnombran: por decision
explicita del encargo, los hallazgos de la serie de IA local conservan el
nombre del proyecto porque son la prueba de que el pipeline funciona.
"""
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dename  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "posts"
BODIES = pathlib.Path("/tmp/tty503-cuerpo")

# slug destino -> (titulo, desc, cat, tags, badge, fecha, [fuentes], desnombrar)
PILLARS = [
    ("sinks-preauth-daemons-c", {
        "title": "Cinco clases de sink pre-auth en daemons C embebidos",
        "desc": ("Del primer paquete de un handshake a un interprete de comandos: cinco "
                 "cadenas reales de inyeccion en daemons C de firmware de router, con la "
                 "clase de vulnerabilidad, el punto de entrada y el alcance honesto de "
                 "cada una. Sin nombres de proyecto: el metodo es lo que se publica."),
        "cat": "Vulnerability Research", "tags": ["CWE-78", "CWE-121", "CWE-125", "RCE pre-auth", "Auditoría"],
        "badge": "rce", "date": "2026-09-02", "dename": True,
        "sources": ["caza-autonoma-e2e-serie", "cadena-portal-cautivo-rce",
                    "fw-host-header-rce", "http-el conversor de fecha a timestamp-stackoverflow",
                    "autopsia-streaming-http-minimo", "suite-paneles-tunel-spooler"],
    }),
    ("cazar-con-ia-local", {
        "title": "Cazar con IA local: pipeline, triaje y seis hallazgos verificados",
        "desc": ("Arquitectura de un sistema de caza autonomo sobre hardware propio, el "
                 "metodo de triaje con doble validacion, y seis hallazgos con "
                 "reproduccion en bibliotecas y demultiplexadores del sistema."),
        "cat": "Vulnerability Research", "tags": ["Automatización", "Triaje", "ASAN", "IA local"],
        "badge": "rce", "date": "2026-08-21", "dename": False,
        "sources": ["sherlock-caza-autonoma-ia-local", "7zip-isfolderencrypted-oob-read",
                    "ffmpeg-demuxers-dos-vpk-vqf-smacker", "libwebp-vp8l-lossless-decode-dos",
                    "pcre2-jit-compile-hang-recursion", "libarchive-cab-lzx-uninitialized-memory"],
    }),
    ("agentes-ia-locales", {
        "title": "Cómo trabajo con agentes de IA locales: arquitectura, memoria y resultados",
        "desc": ("Dos o mas analistas especializados en paralelo sobre la misma pregunta, "
                 "un registro de memoria compartido que indexa hechos y lecciones, y un "
                 "modelo pequeno haciendo el trabajo repetitivo en la propia maquina."),
        "cat": "Agentes", "tags": ["Agentes", "Memoria", "IA local", "Automatización"],
        "badge": "guide", "date": "2026-09-24", "dename": False,
        "sources": ["agentes-locales-arquitectura", "agentes-memoria-aprendizaje",
                    "agentes-resultados-progreso"],
    }),
    ("exploit-development-y-reversing", {
        "title": "Exploit development y reversing: kernel de Windows, ROP de 64 bits y Assembly",
        "desc": ("Bitacora de un mes de laboratorio: internals de Windows, drivers KMDF y "
                 "UMDF, formatos PE/ELF/DEX, convenciones de llamada, construccion de "
                 "shellcode, ROP en 64 bits y heuristicas para identificar funciones."),
        "cat": "Exploit Development", "tags": ["ROP", "Windows internals", "x86-64", "Drivers"],
        "badge": "infra", "date": "2026-06-04", "dename": False,
        "sources": ["exploit-development-lab", "assembly"],
    }),
    ("seguridad-ot-ics", {
        "title": "Seguridad OT: S5/S7, la maquina virtual MC7 y la ausencia de logs en ICS",
        "desc": ("De STEP5/AWL a STEP7, la maquina virtual MC7 y su reversing de bytecodes, "
                 "exploit development sobre PLC, un sandbox escape con ejecucion nativa en "
                 "kernel, ROP sobre MC7 y por que las ICS carecen estructuralmente de "
                 "registro de auditoria."),
        "cat": "Seguridad OT", "tags": ["ICS", "PLC", "AWL", "MC7", "Firmware"],
        "badge": "infra", "date": "2026-06-05", "dename": False,
        "sources": ["plc", "exploit-development-ot-awl-arm"],
    }),
    ("deteccion-blue-team", {
        "title": "Tres tecnicas clasicas y como se detectan: sudo, Windows y evasion de opcodes",
        "desc": ("El mecanismo de cache de sudo como via de persistencia, inyeccion y "
                 "persistencia en Windows, y la reescritura de opcodes que llevo las "
                 "detecciones de 16 a cero con la misma logica. Cada tecnica con los "
                 "indicadores que deja y la regla de deteccion del lado defensivo."),
        "cat": "Blue Team", "tags": ["Detección", "T1548.003", "Auditoría", "MITRE ATT&CK"],
        "badge": "ti", "date": "2026-06-01", "dename": False,
        "sources": ["arte-de-la-paciencia-sudo-cache", "myPracticalShellcodeC2",
                    "evasion-estatica-asm-mirai"],
    }),
    ("fraude-cripto-y-phishing", {
        "title": "Fraude cripto y phishing: dos casos con IoCs y grafo de infraestructura",
        "desc": ("Deconstruccion de un exchange falso con frontend SPA, WebSocket en tiempo "
                 "real y la clave del captcha entregada en el propio JSON, y de una fuga de "
                 "datos por modo depuracion activo en produccion. IoCs, dominios y wallets."),
        "cat": "Threat Intelligence", "tags": ["IoC", "Phishing", "Fraude", "Cloudflare"],
        "badge": "ti", "date": "2026-10-15", "dename": False,
        "sources": ["pigbutchering-bybsusd", "fakewealth-cmdxcapital"],
    }),
    ("phishing-campanas-y-busqueda", {
        "title": ("Campanas de phishing conectadas y el metodo de busqueda de amenazas: "
                  "cuatro investigaciones"),
        "desc": ("Redireccion multi-capa con exfiltracion a canales de mensajeria, una SPA "
                 "con geofencing, y la bitacora de un ano de caza: mapa OSINT de una red "
                 "de estafa, fraude con un stealer, un RAT comercial y un dropper "
                 "multi-etapa. Lo que conecta las cuatro."),
        "cat": "Threat Intelligence", "tags": ["OSINT", "Phishing", "Malware", "IoC"],
        "badge": "ti", "date": "2026-05-24", "dename": False,
        "sources": ["operation-general-jp-silentwarn", "threat-hunter-recollection"],
    }),
    ("laboratorio-de-seguridad", {
        "title": "Laboratorio de seguridad: SOC con honeypots y tuneles ofuscados",
        "desc": ("Montaje completo de un laboratorio Blue Team sobre Proxmox con honeypots, "
                 "contenedores rootless y monitoreo, mas el montaje de un tunel que se "
                 "camufla como TCP con enmascaramiento de IP y DNS cifrado. Arquitectura y "
                 "despliegue automatizado."),
        "cat": "Infraestructura", "tags": ["SOC", "Honeypots", "Túneles", "Proxmox"],
        "badge": "infra", "date": "2026-05-24", "dename": False,
        "sources": ["infra-soc", "infraestructura-tunel-ofuscado"],
    }),
    ("saint-grail", {
        "title": "SAINT GRAIL: plataforma modular de investigacion de seguridad con IA",
        "desc": ("La version reescrita en Go por rendimiento y concurrencia nativa, con dos "
                 "hallazgos reproducibles generados por IA y una validacion debil en un "
                 "gestor de archivos. Codigo publico: arquitectura, integraciones y lo que "
                 "costo reescribirlo."),
        "cat": "Herramientas propias", "tags": ["Go", "Automatización", "Código abierto"],
        "badge": "guide", "date": "2026-07-05", "dename": False,
        "sources": ["saint-grail-go", "saint-grail"],
    }),
    ("analystty", {
        "title": "analystty: triaje automatizado de ejecutables PE con Python",
        "desc": ("Extrae imports, correlaciona TTPs con MITRE ATT&CK, desensambla la seccion "
                 ".text y genera breakpoints para el depurador. Un caso real: un dropper "
                 "que ocultaba sus imports con hashing de API."),
        "cat": "Herramientas propias", "tags": ["Python", "Capstone", "Triaje", "ATT&CK"],
        "badge": "ti", "date": "2026-05-15", "dename": False,
        "sources": ["analystty"],
    }),
    ("pentest-api-jwt-idor", {
        "title": "Pentest a API financiera: IDOR por validacion incompleta de JWT",
        "desc": ("Auditoria donde el backend validaba la firma del token pero no la "
                 "pertenencia del recurso: la criptografia estaba bien, la autorizacion no. "
                 "Recorrido del hallazgo, impacto y como se corrige."),
        "cat": "Pentesting", "tags": ["JWT", "IDOR", "API", "Autorización"],
        "badge": "infra", "date": "2024-08-15", "dename": False,
        "sources": ["web-api-pentesting2024"],
    }),
]

# Los articulos que se van de la portada al ser absorbidos.
ABSORBED = {s for _, d in PILLARS for s in d["sources"]}

# Puentes: una linea que cose las secciones de un pilar multi-fuente.
BRIDGE = {
    "cadena-portal-cautivo-rce": ("Una identidad que llega antes de autenticar y termina "
        "en un interprete de comandos, sin ninguna validacion intermedia."),
    "fw-host-header-rce": ("El mismo patron, distinta entrada: una cabecera de protocolo "
        "que se concatena al construir una regla de firewall."),
    "http-el conversor de fecha a timestamp-stackoverflow": ("Aqui el fallo no es de inyeccion sino de longitud: "
        "un parser de fecha que copia sin limite a un buffer de pila."),
    "autopsia-streaming-http-minimo": ("Dos casos de impacto acotado,included porque son la "
        "leccion: una primitiva real no es automaticamente una cadena."),
    "suite-paneles-tunel-spooler": ("Y cuatro sinks mas, en la suite de administracion "
        "del servidor, donde la pregunta correcta no es si se inyecta sino si se alcanza."),
    "sherlock-caza-autonoma-ia-local": ("La arquitectura del pipeline y, a partir de aqui, "
        "los seis hallazgos que produjo."),
    "7zip-isfolderencrypted-oob-read": "Lectura fuera del heap por un parser que reinterpreta lo que otro ya consumio.",
    "ffmpeg-demuxers-dos-vpk-vqf-smacker": "Tres demultiplexadores donde la entrada manda sobre la aritmetica.",
    "libwebp-vp8l-lossless-decode-dos": "Un guardia que un camino aplica y el otro no.",
    "pcre2-jit-compile-hang-recursion": "El bug no esta en ejecutar el patron, sino en compilarlo.",
    "libarchive-cab-lzx-uninitialized-memory": "Patch-diffing: dos compilaciones del mismo codigo, una sola con el fallo.",
    "plc": "La base: como esta hecho un autómata de la familia S5/S7 y por que se puede invertir.",
    "exploit-development-ot-awl-arm": "Y lo que pasa cuando el reversing se convierte en explotacion.",
    "arte-de-la-paciencia-sudo-cache": "Un script de quince lineas que ya es una brecha.",
    "myPracticalShellcodeC2": "Inyeccion y persistencia en Windows, con los indicadores que dejan.",
    "evasion-estatica-asm-mirai": "Y la otra cara: como se pierde la firma sin cambiar la logica.",
    "pigbutchering-bybsusd": "Un exchange falso con la clave del captcha en el propio JSON.",
    "fakewealth-cmdxcapital": "Y una fuga que solo hacia falta que el modo depuracion quedara activo.",
    "operation-general-jp-silentwarn": "Dos campanas de phishing que se conectan por infraestructura.",
    "threat-hunter-recollection": "Lo que las cuatro investigations tienen en comun y como se busco.",
    "infra-soc": "El laboratorio: aislamiento, honeypots y monitoreo.",
    "infraestructura-tunel-ofuscado": "Y la parte de salida: un tunel que se disfraza de TCP.",
    "saint-grail-go": "La reescritura en Go y por que se hizo.",
    "saint-grail": "La version original y el diseño modular que la precedio.",
    "agentes-locales-arquitectura": "La arquitectura: quien hace que.",
    "agentes-memoria-aprendizaje": "La memoria: como el error de ayer pesa en la decision de hoy.",
    "agentes-resultados-progreso": "Y los resultados, medidos como se pueden medir.",
}


def renumber(body):
    """Renumera las secciones para que el pilar se lea como un articulo unico."""
    n = [0]

    def sub(m):
        n[0] += 1
        title = re.sub(r"^\s*\d+(\.\d+)*[.—\-]?\s*", "", m.group(1)).strip()
        title = re.sub(r"^0x\d+\s*[—\-]\s*", "", title).strip()
        if not title:
            title = "Detalle"
        return f'<h2>{n[0]}. {title}</h2>'
    return re.sub(r"<h2>(.*?)</h2>", sub, body, flags=re.S), n[0]


def strip_chrome(body):
    """Quita el veredicto suelto, los enlaces de vuelta y los titulos duplicados."""
    body = re.sub(r"<p[^>]*>\s*<a[^>]*>[^<]*(Volver|←)[^<]*</a>\s*</p>", "", body, flags=re.S)
    body = re.sub(r"<p[^>]*>\s*(←|Volver al indice)[^<]*</p>", "", body, flags=re.S)
    body = re.sub(r'<(h1|h2)[^>]*>\s*Resumen ejecutivo\s*</\1>', "", body, flags=re.I)
    body = re.sub(r"</?(aside|nav|ul)\b[^>]*>\s*(Indice|Contenidos)?\s*</?(aside|nav|ul)>", "", body)
    return body.strip()


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    index = {}
    for slug, d in PILLARS:
        parts, total = [], 0
        for i, src in enumerate(d["sources"]):
            path = BODIES / f"{src}.html"
            if not path.exists():
                # los pilares P3 son posteriores al historico: no tienen version
                # larga recuperable, se usa el cuerpo condensado que ya existia.
                path = ROOT / "src" / "legacy" / f"{src}.html"
            if not path.exists():
                print(f"  FALTA {src}")
                continue
            body = path.read_text(encoding="utf-8")
            if d["dename"]:
                body = dename.dename(body)
            body = strip_chrome(body)
            if i > 0 and src in BRIDGE:
                parts.append(f'<p class="resumen"><strong>Continuidad.</strong> {BRIDGE[src]}</p>')
            parts.append(body)
        merged = "\n\n".join(p for p in parts if p.strip())
        merged, nsec = renumber(merged)
        merged = re.sub(r"\n{3,}", "\n\n", merged).strip()
        hits = dename.audit(merged) if d["dename"] else {}
        if hits:
            print(f"  !! {slug} conserva referencias: {hits}")
        (SRC / f"{slug}.html").write_text(merged + "\n", encoding="utf-8")
        w = len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", merged)))
        index[slug] = {"sections": nsec, "words": w, "denamed": d["dename"],
                       "sources": d["sources"]}
        print(f"{w:>6} palabras  {nsec:>3} secciones  "
              f"{'[desnombrado]' if d['dename'] else '            '}  {slug}")
    (pathlib.Path(__file__).parent / "pillar_index.json").write_text(json.dumps(index, indent=2))
    print(f"\n{len(index)} pilares, {sum(v['words'] for v in index.values())} palabras")


if __name__ == "__main__":
    main()
