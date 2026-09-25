# Fuentes legacy

Cuerpos condensados de articulos que nacieron despues del ultimo commit con
version larga en el historial, y que por tanto **no se pueden recuperar** de
git. `tools/assemble_pillars.py` los usa como fuente para construir
`agentes-ia-locales.html`.

El commit 5a34273 condenso todo el sitio a ~270 palabras por articulo. Para
todos los demas pilares el material largo se extrae del historial
(`tools/extract_bodies.py`); para estos cuatro no existe esa version.
