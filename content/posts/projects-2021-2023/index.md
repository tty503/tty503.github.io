---
title: "DevLog : Reversing, Hardware y la construcción de un Laboratorio"
date: 2024-11-19
draft: false
tags: ["Malware Analysis", "Ghidra", "Djvu", "PCB Design", "Infrastructure", "INetSim", "C2 Development"]
categories: ["DevLog", "Portafolio"]
author: "Christian Marquez"
description: "Una crónica técnica de mi evolución: del reversing de software y diseño de PCBs, a la gestión de infraestructura limitada y automatización de análisis."
---

El camino para entender la ciberseguridad ofensiva y defensiva rara vez es una línea recta. Entre 2021 y 2023, mi enfoque osciló entre el **software de alto nivel**, el **bajo nivel**  y, eventualmente, la **capa física** y la infraestructura que sostiene todo esto.

Este *DevLog* documenta cronológicamente los proyectos, los errores y los aprendizajes de esos años.

## 2021: Rompiendo el hielo con el Reversing

Mis inicios estuvieron marcados por la resolución de desafíos de ingeniería inversa, específicamente los de **MalwareTech**. En esta etapa, el objetivo era simple pero fundamental: entender cómo un binario oculta sus secretos.

Pasé horas trazando la ejecución en debuggers, aprendiendo a identificar estructuras de datos en memoria y "cazando" flags ofuscadas.

<img src="/img/projects-2021-2023/post-1.jpg" alt="Resolviendo flags de strings básico en desafíos CTF" width="800" height="400" />
<img src="/img/projects-2021-2023/post-5.jpg" alt="MalwareTech CTF" width="800" height="400" />

Rápidamente, la necesidad de herramientas más potentes me llevó a **Ghidra** e **IDA Pro**. No bastaba con ver el código ensamblador; necesitaba entender el flujo de control global. Aquí, por ejemplo, analicé cómo un binario calculaba hashes MD5 para validar su integridad o verificar claves, una técnica común en malware para evitar ser modificado.

<img src="/img/projects-2021-2023/post-6.jpg" alt="Análisis estático inicial en IDA Pro mostrando strings referenciadas" width="800" height="400" />
<img src="/img/projects-2021-2023/post-10.jpg" alt="Vista de decompilación en Ghidra analizando rutinas de hash" width="800" height="400"/>

## 2022: La Trinchera del Malware (Djvu & BazarBackdoor)

Con los fundamentos claros, salté al análisis de amenazas reales. Mi proyecto más largo fue el seguimiento del **Ransomware Djvu**. Durante meses, documenté sus variantes entre 2020 y 2022.

Uno de los mayores retos fue analizar la **entropía de las secciones**. El malware moderno suele venir "empaquetado" (packed) para evadir antivirus. Visualizar la entropía me permitía identificar rápidamente qué secciones contenían código cifrado o comprimido, diferenciando el *loader* del *payload* real.

<img src="/img/projects-2021-2023/post-4.jpg" alt="Análisis de entropía y secciones PE en Djvu Ransomware" width="800" height="400" />

Posteriormente, al analizar **BazarBackdoor**, el enfoque cambió de "¿cómo funciona el binario?" a "¿qué quiere el atacante?".

Correlacioné el código desensamblado con las TTPs (Técnicas, Tácticas y Procedimientos) de reconocimiento de red. Descubrí que el malware ejecutaba comandos específicos de **PowerShell** y **CMD** para enumerar usuarios del Directorio Activo. Mapear estas instrucciones a comandos como `net users /img/projects-2021-2023/domain` o `Get-ADUser` fue clave para entender el impacto operativo de la infección.

<img src="/img/projects-2021-2023/post-12.jpg" alt="Correlación de código de BazarBackdoor con comandos de enumeración de AD" width="800" height="400" />

Todo este análisis manual desembocó en la creación de documentación técnica y reglas YARA para la detección proactiva.

<img src="/img/projects-2021-2023/post-2.jpg" alt="Reporte técnico y reglas YARA basadas en el análisis" width="800" height="400" />

## Infraestructura: Cuando el Hardware es el Límite

Montar un laboratorio de análisis de malware requiere recursos. Necesitas aislar la amenaza en una red virtual controlada, simular servicios de internet y ejecutar herramientas pesadas.

Me topé con la realidad del hardware limitado. Al intentar correr **INetSim** (para simular respuestas DNS/img/projects-2021-2023/HTTP y engañar al malware creyendo que tiene internet) junto con máquinas víctimas en un entorno virtualizado, la memoria RAM se convirtió en un cuello de botella crítico.

Aprendí a optimizar servicios en Debian y a trabajar en *Low Memory Mode*, gestionando cada megabyte para mantener el laboratorio operativo sin colgar el host.

<img src="/img/projects-2021-2023/post-15.jpg" alt="Debian ejecutando INetSim en modo de baja memoria" width="800" height="400" />

## 2023: Descendiendo al Hardware (PCB)

En febrero de 2023, mi curiosidad técnica se expandió hacia el hardware. En el trabajo, recibí una inducción sobre **diseño de PCBs** (Circuitos Impresos).

Aunque mi perfil es de software, entender cómo se diseñan los circuitos, cómo se ubican los componentes y cómo fluyen las señales eléctricas me dio una nueva perspectiva sobre la seguridad en sistemas embebidos y IoT. Es el nivel más bajo posible: donde el código se encuentra con el silicio.

<img src="/img/projects-2021-2023/post-14.jpg" alt="Diseño de PCB y visualización 3D de componentes electrónicos" width="800" height="400" />

## Desarrollo Ofensivo: C, Bits y C2

De vuelta al código, me obsesioné con entender cómo el malware interactúa con el sistema operativo a bajo nivel. Profundicé en **C** y las operaciones *bitwise* (desplazamientos, máscaras XOR, AND/img/projects-2021-2023/OR), esenciales para entender algoritmos de cifrado y ofuscación de strings.

<img src="/img/projects-2021-2023/post-8.jpg" alt="Código C: Implementación de máscaras y desplazamiento de bits" width="800" height="400" />
<img src="/img/projects-2021-2023/post-9.jpg" alt="Snippet de C mostrando lógica de manipulación de bytes" width="800" height="400" />
<img src="/img/projects-2021-2023/post-7.jpg" alt="Bitwise snippet" width="800" height="400" />


Paralelamente, seguí mejorando mis habilidades de SysAdmin utilizando **OpenBSD** y automatizando configuraciones con **Ansible**, buscando siempre la simplicidad y seguridad por diseño.

<img src="/img/projects-2021-2023/post-11.jpg" alt="Automatización de servidores OpenBSD con Ansible" width="800" height="400" />

## El Presente: Analystty

Toda esta experiencia —el dolor de cabeza con la gestión de memoria, el análisis manual tedioso de Djvu y la comprensión del código de bajo nivel— culminó con : **Analystty**.

Es una herramienta CLI en Python que automatiza lo que antes me tomaba horas: parsear cabeceras PE, detectar capacidades maliciosas y resolver direcciones de memoria dinámicamente.


<img src="/img/projects-2021-2023/post-3.jpg" alt="Código fuente en Python para la automatización del análisis" width="800" height="400" />

Este viaje me enseñó que la especialización es importante, pero tener una visión general —desde el diseño de la placa base hasta el script de automatización— es lo que realmente te da ventaja en ciberseguridad.
