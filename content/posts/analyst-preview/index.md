---
title: "Automatizando la Disección de Binarios: preview de analystty"
date: 2024-10-30
draft: false
tags: ["Malware Analysis", "Python", "Reverse Engineering", "Automation", "Assembly", "x64dbg"]
categories: ["Proyectos", "Desarrollo"]
author: "Christian Marquez"
description: "Cómo transformé una colección de scripts de análisis en una herramienta CLI capaz de identificar TTPs y resolver direccionamiento relativo en x64."
---

El análisis de malware suele comenzar como un proceso manual y meticuloso. Sin embargo, cuando te enfrentas a un lote de muestras (como el set de *Bazaar 2020.02* con el que he estado trabajando), la repetición se vuelve el enemigo.

Desde julio de 2024, he estado trabajando en **Analystty**, un proyecto personal que nació de una necesidad simple: dejar de repetir las mismas tareas básicas en cada binario. Lo que comenzó como scripts de Python dispersos para analizar cabeceras PE, hoy es una herramienta CLI en desarrollo que busca cerrar la brecha entre el análisis estático y el dinámico.

## El Problema: Escalar el Análisis

Cuando analizas una muestra de ransomware (como las variantes de *Djvu* que se ven en las capturas), el primer paso es siempre el mismo: identificar secciones, buscar importaciones sospechosas y mapear dónde se usan. Hacer esto manualmente en un desensamblador para 50 archivos no es viable.

<img src="/img/analystty-preview/post-5.jpg" alt="Entorno de desarrollo con VS Code y FlareVM" width="1000" height="400" />

## 1. Análisis Estático y Detección de Capacidades

El núcleo de la herramienta utiliza `pefile` y `capstone` para diseccionar el binario. No me interesaba solo ver las importaciones, sino **clasificarlas**. Implementé un sistema de etiquetado (basado en un `config.json` y listas de *MalApi*) que categoriza las funciones automáticamente.

Si el malware importa `VirtualProtect` o `WriteProcessMemory`, la herramienta lo etiqueta inmediatamente como **Injection** o **Evasion**.

<img src="/img/analystty-preview/post-1.jpg" alt="Detección de APIs de Malware" width="800" height="600" />

Esto me permite obtener una "radiografía" rápida de las intenciones del binario antes de siquiera abrir un debugger.

## 2. El Desafío de x64: Resolviendo RIP-Relative Addressing

Aquí es donde entra la parte de **Desarrollo de Software** aplicada a la ingeniería inversa. En arquitecturas x86 (32 bits), encontrar una llamada a una API suele ser directo. Pero en x64, el código hace un uso extensivo del direccionamiento relativo al puntero de instrucción (RIP).

Ver una instrucción como `call qword ptr [rip + 0x6e58]` no te dice mucho a simple vista. Para saber a qué función está llamando realmente el malware, necesitas calcular ese offset.

<img src="/img/analystty-preview/post-6.jpg" alt="Output offsets" width="800" height="600" />


Implementé una lógica en `analystty.py` usando expresiones regulares y aritmética hexadecimal para resolver esto estáticamente:

<font size="1">

```python
if mnemonic in ['call', 'jmp']:
    # Agregar la capacidad de distinguir otros registros, 
    # la misma logica es usada para ubicar los argumentos 
    # que son cargandos en la funcion. Ademas, debe tener 
    # la capacidad de adaptarse en caso de que sea 32 bits.
    if operands == 'rax':
        match = re.search(r'\[rip\s*([\+\-])\s*0x([0-9a-fA-F]+)\]', previous['OPERATORS'])
    else:
        match = re.search(r'\[rip\s*([\+\-])\s*0x([0-9a-fA-F]+)\]', operands)
    if match:
        # No hemos considerado la posibilidad de que use mas 
        # elementos para calcular el offset debemos poder detectar 
        # cuando se esta realizan un calculo de offset. 
        # Una idea podria ser encontrar la instruccion call equivalente, 
        # identificar el registro en donde se carga la direccion calculada 
        # y tracear hacia atras para saber que valores estuvieron involucrados en el calculo. 
        offset = int(match.group(1) + match.group(2), 16)
        address = hex(int(address, 16) + offset)
```

</font>

El script parsea el desensamblado, busca patrones [rip + offset], calcula la dirección física final y la cruza con la tabla de importaciones (IAT). La herramienta resolviendo automáticamente que [rip + 0x6e58] corresponde a Sleep y [rip + 0x6e55] a WinExec.

Gracias a esto, puedo generar una tabla limpia que me dice exactamente en qué dirección de memoria se está invocando una función crítica. La visualización final de las llamadas resueltas: Dirección de inicio, Dirección de la instrucción y la API objetivo.

<img src="/img/analystty-preview/post-7.jpg" alt="Tabla limpia" width="800" height="400" />

El objetivo final de esta automatización no es solo imprimir texto en consola, sino preparar el terreno para el debugging.

La clase medbg dentro de la herramienta está diseñada para interactuar con x64dbg. Utilizando la información recolectada estáticamente (los Entry Points y los offsets de las APIs maliciosas calculados anteriormente), el script puede:

* Conectarse al debugger.
* Calcular la dirección base dinámica (ASLR).
* Colocar breakpoints automáticamente en las llamadas a funciones de interés (como Sleep, WinExec o IsDebuggerPresent).

<img src="/img/analystty-preview/post-9.jpg" alt="Tabla resultante para el MalApi" width="800" height="400" />

x64dbg con breakpoints establecidos automáticamente por el script en el EntryPoint y en las llamadas a APIs críticas.

Sin embargo, este proyecto aun esta en desarrollo en [github](https://github.com/tty503/analystty) puedes conseguir el sketch sin actualizar pero pronto espero subir una version completa.