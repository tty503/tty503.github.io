#!/usr/bin/env python3
"""Desnombrado: sustituye nombres de producto y nombres de fichero interno por
descripciones funcionales, para poder publicar el metodo sin publicar el target.

Criterio (dos niveles, aplicados por este script):

  1. IDENTIFICADORES DEL PRODUCTO -> descripcion funcional generica.
     el daemon de portal cautivo, el daemon de autenticacion y redireccion, el servidor HTTP embebido, el servidor HTTP minimo, el panel web de administracion del servidor, el panel web de administracion restringida, el daemon de tunel L2TP/IPsec,
     el spooler de impresion, la biblioteca cliente del protocolo de streaming. Tambien los nombres de fichero internos que aparecen en las
     tablas de evidencia (el modulo de portal cautivo, el script de alta de sesion, conup, la herramienta de configuracion de impresorasrip, el CGI de administracion,
     el gestor de credenciales.c, el conversor de fecha a timestamp, fw_iptables.c, miniserv): un archivo:línea con el
     nombre del proyecto reidentifica el blanco tan eficazmente como el titulo.

  2. NO SE TOCA: nombres de estandar y de protocolo (EAP, RADIUS, 802.1X, L2TP,
     RTMP, AMF3, iptables, SSL). Son especificaciones publicadas que implementa
     una decena de fabricantes distintos; keep them or el articulo deja de
     ser util. Lo que se anonimiza es el software, no la norma.

Decision adicional que se toma aqui y que hay que declarar al lector: tambien
se neutraliza el nombre de la distribucion de firmware. El encargo listaba nueve
proyectos, pero "firmware de router de codigo abierto" + "daemon de portal
cautivo que construye reglas de iptables" + "servidor HTTP embebido" identifica
el blanco de forma trivial aunque no aparezca ni un nombre propio. Mantenerlo
dejaria el desnombrado decorativo.

Salida: el texto es el mismo, con los nombres sustituidos. No se anade, se quita
nada. Lo que el lector pierde es la capacidad de repetir el hallazgo contra el
producto concreto; lo que conserva es el metodo, que es lo que se publica.
"""
import pathlib
import re
import sys

# Orden importa: se aplican de mas largo a mas corto para que "el daemon de portal cautivo RADIUS"
# no se parcialice en "el daemon de portal cautivo" + " RADIUS".
MAP = [
    # --- Panel web de administracion -------------------------------------
    (r"el panel web de administracion del servidor", "el panel web de administración del servidor"),
    (r"el panel web de administracion restringida", "el panel web de administración restringida"),
    (r"miniserv-lib\.pl", "la biblioteca del servidor web de administración"),
    (r"miniserv\.conf", "el fichero de configuración del servidor web de administración"),
    (r"miniserv", "el servidor web de administración"),
    (r"cpan/install\.cgi", "el instalador de módulos del lenguaje, vía web"),
    (r"install\.cgi", "el instalador de módulos, vía web"),
    (r"setup\.cgi", "el script de configuración por web"),
    (r"find\.cgi", "el buscador de ficheros por web"),
    (r"CPAN", "el gestor de módulos del lenguaje"),
    (r"cpan", "el gestor de módulos del lenguaje"),
    (r"Uwsgi", "el servidor de aplicaciones"),

    # --- Spooler de impresion ------------------------------------------
    (r"el spooler de impresion-browsed", "el navegador de impresoras"),
    (r"cupsICCProfile", "el perfil de color de la impresora"),
    (r"la herramienta de configuracion de impresoras-rip", "el generador de filtros de impresión"),
    (r"la herramienta de configuracion de impresorasrip", "el generador de filtros de impresión"),
    (r"CUPSF", "el filtro de la impresora"),
    (r"el spooler de impresion", "el spooler de impresión"),
    (r"el spooler de impresion", "el spooler de impresión"),

    # --- Daemon de tunel L2TP/IPsec ------------------------------------
    (r"el daemon de tunel L2TP/IPsec", "el daemon de túnel L2TP/IPsec"),
    (r"pppd_compat", "la capa de compatibilidad del demonio de túnel"),
    (r"pppd", "el demonio de túnel"),
    (r"ip-up", "el script de subida de interfaz"),
    (r"ip-up\.script", "el script de subida de interfaz"),

    # --- Biblioteca cliente RTMP ----------------------------------------
    (r"la biblioteca cliente del protocolo de streaming", "la biblioteca cliente del protocolo de streaming"),
    (r"el volcador de flujos del protocolo", "el volcador de flujos del protocolo"),
    (r"AMF3_ReadNumber", "la routine de lectura de numero del decodificador"),
    (r"AMF3_ReadString", "la routine de lectura de cadena del decodificador"),
    (r"AMFObject", "el objeto contenedor del formato"),
    (r"AMF3\b", "el decodificador del formato de serialización"),
    (r"AMF", "el formato de serialización"),
    (r"RTMP", "el protocolo de streaming"),
    (r"AMF0\b", "la variante elemental del formato"),

    # --- Portal cautivo: RADIUS ----------------------------------------
    (r"el servidor RADIUS", "el servidor RADIUS"),
    (r"el daemon de portal cautivo", "el daemon de portal cautivo"),
    (r"prueba_de_escritorio", "el caso de laboratorio"),
    (r"el daemon de portal cautivo", "el portal cautivo"),
    (r"el daemon de portal cautivo\.c", "el módulo de protocolo del daemon"),
    (r"el daemon de portal cautivo\.log", "el registro del daemon"),
    (r"enable-el daemon de portal cautivoscript", "el activador del script de sesión"),
    (r"el daemon de portal cautivo_Dir", "el directorio de sesión"),
    (r"el daemon de portal cautivo", "el daemon de portal cautivo"),
    (r"conup", "el script de alta de sesión"),
    (r"up\.sh", "el script de alta de sesión"),
    (r"USER_NAME", "la variable de entorno con la identidad"),
    (r"freeradius", "otro servidor RADIUS"),
    (r"RADIUS", "RADIUS"),
    (r"EAP-Response/Identity", "respuesta EAP-Identity"),
    (r"EAP-Identity", "EAP-Identity"),
    (r"EAP-Request", "peticion EAP"),
    (r"EAPOL-Start", "EAPOL-Start"),
    (r"poc_eap_identity\.py", "el guion de prueba"),
    (r"EAP", "EAP"),
    (r"\b802\.1X", "802.1X"),

    # --- Portal cautivo: auth/redireccion ------------------------------
    (r"el daemon de autenticacion y redireccion\.conf", "la configuración del daemon"),
    (r"el daemon de autenticacion y redireccion", "el daemon de autenticación y redirección"),
    (r"libhttpd", "el servidor HTTP embebido"),
    (r"FirewallRuleSet", "el conjunto de reglas de firewall"),
    (r"fw3\b", "el generador de reglas de firewall"),
    (r"fw_iptables\.c", "el módulo de reglas de firewall"),
    (r"iptables", "iptables"),

    # --- Servidor HTTP embebido ----------------------------------------
    (r"el servidor HTTP embebido\.c", "el módulo del servidor HTTP"),
    (r"el servidor HTTP embebido\.?\b", "el servidor HTTP embebido"),
    (r"el servidor HTTP minimo\.c", "el módulo del servidor HTTP mínimo"),
    (r"el servidor HTTP minimo", "el servidor HTTP mínimo"),
    (r"el servidor HTTP minimo", "el servidor HTTP mínimo"),
    (r"el conversor de fecha a timestamp", "el conversor de fecha a timestamp"),
    (r"If-Modified-Since", "If-Modified-Since"),
    (r"el gestor de credenciales\.c", "el generador de credenciales"),
    (r"el gestor de credenciales", "el generador de credenciales"),

    # --- Distribucion de firmware (neutralizada: ver docstring) --------
    (r"la distribucion de firmware", "el firmware de router de código abierto"),
    (r"build la distribucion de firmware", "la compilación del firmware de router"),

    # --- Cabeceras de confianza -----------------------------------------
    (r"X-SSL-Client-Cert-DN", "X-SSL-Client-Cert-DN"),
    (r"X-SSL-Client-\*", "X-SSL-Client-*"),
    (r"trust_real_ip", "la opción de confiar en la IP real"),
]

# Comprobacion: ningun termino prohibido debe sobrevivir.
FORBIDDEN = [
    "el daemon de portal cautivo", "el daemon de portal cautivo", "el daemon de portal cautivo", "el daemon de autenticacion y redireccion", "el servidor HTTP embebido", "el servidor HTTP minimo",
    "el servidor HTTP minimo", "el panel web de administracion del servidor", "el panel web de administracion restringida", "el daemon de tunel L2TP/IPsec", "el daemon de tunel L2TP/IPsec", "el spooler de impresion",
    "la biblioteca cliente del protocolo de streaming", "el volcador de flujos del protocolo", "conup", "el script de alta de sesion", "el modulo de portal cautivo", "fw_iptables",
    "la herramienta de configuracion de impresoras", "el gestor de credenciales", "el conversor de fecha a timestamp", "miniserv", "el CGI de administracion",
    "el CGI de administracion", "el CGI de administracion", "la distribucion de firmware", "freeradius", "prueba_de_escritorio",
]


# Arreglos de prosa. Una sustitucion mecanica es ciega a la gramatica: produce
# "un respuesta", "(antes el daemon de portal cautivo )" y
# "/etc/el daemon de portal cautivo/el script". Se corrigen a mano los
# artefactos que se han detectado, y se verifican con audit() despues.
#
# El cuerpo recuperado envuelve palabras en <b>, <code> y <em>, de modo que
# "un respuesta" puede llegar al regex como "un <code>respuesta</code>". Por eso
# una "palabra" se compone como etiqueta?+ espacio? palabra espacio? etiqueta?+,
# que acepta las tres formas: desnuda, etiquetada por delante o por detras.
TAG = r"(?:</?(?:b|code|em|strong|i|span)\b[^>]*>\s*)*"


def W(word):
    return TAG + r"\s*" + word + r"\b"


FIXUPS = [
    (r"\(antes\s*" + W(r"el daemon de portal cautivo") + TAG + r"\s*\)", ""),
    (r"variable de entorno\s*" + W(r"la variable de entorno con la identidad"),
     "variable de entorno con la identidad"),
    (r"/etc/el daemon de portal cautivo/el script de alta de sesión",
     "el script de alta de sesión del daemon"),
    (r"build el firmware de router de código abierto",
     "la compilación del firmware de router"),
    (r"build", "compilación"),
    (r"un\s*" + W(r"respuesta"), "una respuesta"),
    (r"un\s*" + W(r"peticion"), "una petición"),
    (r"un\s*" + W(r"petición"), "una petición"),
    (r"el\s*" + W(r"identity"), "la identidad"),
    (r"El\s*" + W(r"identity"), "La identidad"),
    (r"\b(Ese|ese|el|un|alg\u00fan|alg\u00fan|cada|este)\s*" + W("identity"),
     r"\1 la identidad"),
    (r"\(\s*\)", ""),
    (r"\s+([.,;:!?])", r"\1"),
    (r"\(\s+", "("),
    (r"\s+\)", ")"),
    (r"\s{2,}", " "),
    (r"\n\s*", "\n"),
    (r"\n{3,}", "\n\n"),
]


IMG_RENAME = {
    "el daemon de portal cautivo-eap-phase1-wire": "cadena-01-paquete",
    "el daemon de portal cautivo-eap-phase2-radius": "cadena-02-radius",
    "el daemon de portal cautivo-eap-phase3-rce": "cadena-03-sink",
    "el daemon de portal cautivo-eap-phase4-root": "cadena-04-shell",
    "el daemon de portal cautivo-eap-final-validated": "cadena-05-validado",
    "el daemon de autenticacion y redireccion-phase2-listener": "fw-01-listener",
    "el daemon de autenticacion y redireccion-phase3-injection": "fw-02-inyeccion",
    "el daemon de autenticacion y redireccion-phase4-exploit": "fw-03-comando",
    "el daemon de autenticacion y redireccion-phase5-root-shell": "fw-04-shell",
    "el servidor HTTP embebido-phase1-sink": "http-01-sink",
    "el servidor HTTP embebido-phase3-up": "http-02-desborde",
    "el servidor HTTP embebido-phase4-exploit": "http-03-rop",
    "el servidor HTTP embebido-phase5-shell": "http-04-shell",
}


def rename_imgs(text):
    """Renombra las rutas de imagen ANTES de cualquier sustitucion.

    Un nombre de fichero de imagen identifica el blanco igual que el titulo, y
    estas imagenes se nombraban con el proyecto. Se renombran aqui, en un paso
    explicito y verificable, en lugar de confiar en que las sustituciones
    posteriores respeten el atributo src: "el daemon de portal cautivo-eap-phase1-wire.png" se
    convierte en "cadena-01-paquete.png" y a partir de ahi ninguna sustitucion
    puede tocarlo, porque el nombre ya no contiene ningun termino prohibido.
    """
    def sub(m):
        base = m.group(3).rsplit(".", 1)[0]
        new = IMG_RENAME.get(base)
        return f'{m.group(1)}{m.group(2)}{new}.png' if new else m.group(0)
    return re.sub(r'(src=")(img/)([^"]+)', sub, text)


def dename(text):
    # Los enlaces internos a articulos que van a desaparecer se deshilachan
    # PRIMERO. Los href contienen el slug viejo, que es el nombre del proyecto:
    # si se sustituyeran antes, "cadena-portal-cautivo-rce.html" se
    # convertiria en una cadena con espacios y acentos que no es ni una URL ni
    # un enlace roto que se pueda limpiar despues. Mismo criterio que las
    # imagenes: los atributos se resuelven antes de tocar el texto.
    text = re.sub(r'<a href="[^"]*\.html"[^>]*>(.*?)</a>', r"\1", text, flags=re.S)
    text = rename_imgs(text)
    for pat, rep in MAP:
        text = re.sub(pat, rep, text)
    for pat, rep in CASE_INSENSITIVE:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    for pat, rep in FIXUPS:
        text = re.sub(pat, rep, text)
    return text


# Nombres de producto que deben morir sin importar como esten escritos.
CASE_INSENSITIVE = [
    (r"el daemon de portal cautivo", "el daemon de portal cautivo"),
    (r"el servidor RADIUS", "el servidor RADIUS"),
    (r"el daemon de portal cautivo", "el portal cautivo"),
    (r"el daemon de autenticacion y redireccion", "el daemon de autenticación y redirección"),
    (r"el servidor HTTP embebido", "el servidor HTTP embebido"),
    (r"mini_?httpd", "el servidor HTTP mínimo"),
    (r"el panel web de administracion del servidor", "el panel web de administración del servidor"),
    (r"el panel web de administracion restringida", "el panel web de administración restringida"),
    (r"accel-?ppp", "el daemon de túnel L2TP/IPsec"),
    (r"el spooler de impresion-?browsed", "el navegador de impresoras"),
    (r"el spooler de impresion", "el spooler de impresión"),
    (r"la biblioteca cliente del protocolo de streaming", "la biblioteca cliente del protocolo de streaming"),
    (r"la distribucion de firmware", "el firmware de router de código abierto"),
    (r"conup", "el script de alta de sesión"),
    (r"up\.sh", "el script de alta de sesión"),
    (r"el conversor de fecha a timestamp", "el conversor de fecha a timestamp"),
    (r"el gestor de credenciales", "el generador de credenciales"),
    (r"miniserv", "el servidor web de administración"),
    (r"la herramienta de configuracion de impresoras-?rip", "el generador de filtros de impresión"),
]


def audit(text):
    low = text.lower()
    return {t: low.count(t) for t in FORBIDDEN if t in low}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "audit":
        for f in sys.argv[2:]:
            t = pathlib.Path(f).read_text(encoding="utf-8")
            hits = audit(t)
            print(f"{f}: {'LIMPIO' if not hits else hits}")
    else:
        for f in sys.argv[2:]:
            p = pathlib.Path(f)
            p.write_text(dename(p.read_text(encoding="utf-8")), encoding="utf-8")
            print("denamed", f)
