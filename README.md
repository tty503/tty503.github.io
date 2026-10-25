# tty503.com

Sitio personal de Christian Márquez (tty503): investigador de seguridad autodidacta en Venezuela. Reversing, malware, vulnerabilidades y OT/ICS.

## Contenido

- `index.html` — página principal (diseño terminal, contenido CV + bitácora).
- `img/tty503.jpg` — imagen de identidad del sitio.
- `pgp/tty503.asc` — clave pública PGP.
- `pgp/site.txt` y `pgp/site.txt.asc` — declaración de identidad firmada.
- `index.html.asc` — firma detached de `index.html`.
- `llms.txt` — resumen legible por LLMs.
- `robots.txt`, `sitemap.xml`, `.well-known/security.txt` — indexación y contacto de seguridad.
- `CNAME` — dominio `tty503.com`.
- `404.html` — página de error.

## Vista local

```sh
python3 -m http.server 8000
# http://localhost:8000/
```

## Verificar la firma

```sh
gpg --import pgp/tty503.asc
gpg --verify < pgp/site.txt.asc
gpg --verify index.html.asc index.html
```

Fingerprint:

```text
DE68 AA7C F75E D73B 35A5 92DA B237 FD25 B8E3 D2A7
```

Clave usada: `tty503 <tty503@proton.me>` (RSA 4096, creada 2026-10-13).

## Re-firmar después de editar

Cada cambio en `index.html` invalida la firma detached. Para regenerarla:

```sh
gpg --batch --yes --armor --digest-algo SHA512 \
  --detach-sign -u DE68AA7CF75ED73B35A592DAB237FD25B8E3D2A7 \
  -o index.html.asc index.html
gpg --verify index.html.asc index.html
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
git commit -m "Renovar sitio: diseño terminal, CV + bitácora, SEO y firma PGP"
git push origin main
```
