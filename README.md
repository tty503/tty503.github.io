# tty503.com

Sitio personal de Christian Márquez (tty503): investigador de seguridad autodidacta en Venezuela. Reversing, malware, vulnerabilidades y OT/ICS.

## Estructura

- `index.html` — gateway que detecta el idioma del navegador y enlaza las seis versiones.
- `es/`, `en/`, `zh/`, `ru/`, `he/`, `ar/` — sitio completo en español, inglés, chino, ruso, hebreo y árabe.
- `img/tty503.jpg` — imagen de identidad del sitio.
- `pgp/tty503.asc` — clave pública PGP.
- `pgp/site.txt` y `pgp/site.txt.asc` — declaración de identidad firmada.
- `<idioma>/index.html.asc` — firma detached de cada página.
- `llms.txt` — resumen legible por LLMs.
- `robots.txt`, `sitemap.xml`, `.well-known/security.txt` — indexación y contacto de seguridad.
- `CNAME` — dominio `tty503.com`.
- `404.html` — página de error con selector de idioma.

El gateway redirige según `navigator.languages`. La preferencia se guarda en `localStorage` y se puede evitar la redirección con `https://tty503.com/?stay=1`.

## Vista local

```sh
python3 -m http.server 8000
# http://localhost:8000/?stay=1
```

## Verificar la firma

```sh
gpg --import pgp/tty503.asc
gpg --verify < pgp/site.txt.asc
cd es && gpg --verify index.html.asc index.html
```

Fingerprint:

```text
DE68 AA7C F75E D73B 35A5 92DA B237 FD25 B8E3 D2A7
```

Clave usada: `tty503 <tty503@proton.me>` (RSA 4096, creada 2026-10-13).

## Re-firmar después de editar

Cada cambio en una página invalida su firma detached. Para regenerarla:

```sh
cd es
gpg --batch --yes --armor --digest-algo SHA512 \
  --detach-sign -u DE68AA7CF75ED73B35A592DAB237FD25B8E3D2A7 \
  -o index.html.asc index.html
gpg --verify index.html.asc index.html
```

Repite en `en/`, `zh/`, `ru/`, `he/` y `ar/`, y firma también el gateway:

```sh
gpg --batch --yes --armor --digest-algo SHA512 \
  --detach-sign -u DE68AA7CF75ED73B35A592DAB237FD25B8E3D2A7 \
  -o index.html.asc index.html
```

Si cambia la declaración de identidad (`pgp/site.txt`), vuelve a firmarla:

```sh
gpg --batch --yes --armor --digest-algo SHA512 \
  --clearsign -u DE68AA7CF75ED73B35A592DAB237FD25B8E3D2A7 \
  -o pgp/site.txt.asc pgp/site.txt
```

## Publicación

El repositorio se publica con GitHub Pages desde la rama `main`. El archivo `CNAME` mantiene el dominio `tty503.com`.

```sh
git add .
git commit -m "Sitio multilingüe: gateway por idioma, contenido reducido y firma PGP"
git push origin main
```
