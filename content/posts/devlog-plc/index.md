---
title: "DevLog : comprendiendo la seguridad OT investigación de PLCs S5 a S7"
date: 2025-04-26
draft: false
tags: ["ICS Security", "Siemens S5", "Hardware Hacking", "Scada", "AWL", "Assembly", "Reverse Engineering", "Stuxnet", "Shellcode", "MC7", "Virtual Machine", "S7-300"]
categories: ["DevLog", "Research"]
author: "Christian Marquez"
description: "Inicio de la bitácora de investigación: Análisis físico de PLCs de 1974, diferencias entre estructuras compactas y modulares, y cómo el hardware define el mapa de memoria."
---

El camino para entender la seguridad ofensiva en infraestructuras críticas a menudo comienza mirando hacia atrás. Entre febrero y abril de 2025, mi investigación se centró en diseccionar la "caja negra" que controla la industria: los Controladores Lógicos Programables (PLC).

Lo que comenzó como un curso básico de programación en equipos Siemens S5 legados (algunos datan de 1974), se transformó rápidamente en un proyecto de ingeniería inversa. La primera impresión al llegar al laboratorio fue la de estar en un museo funcional; máquinas corriendo software sobre interfaces que recordaban a Windows 95, controlando procesos físicos reales.

<img src="/img/devlog-plc/post-2.jpg" alt="HMI/SCADA antiguo monitoreando procesos físicos en tiempo real" width="800" height="400" />

Sin embargo, tocar el hardware real ofrece una perspectiva que ningún simulador puede igualar. Ver una válvula abrirse físicamente te hace consciente del impacto cinético del código. No es solo un cambio de bit en un registro; es una acción en el mundo físico.

### Anatomía del Hardware: Modular vs. Compacto

Para un atacante (o un ingeniero reverso), entender el factor de forma es crucial porque define cómo se direcciona la memoria. En la familia Siemens S5, encontramos dos arquitecturas principales:
<img src="/img/devlog-plc/post-10.png" alt="Arquitectura de S5" width="800" height="400" />

#### 1. Estructura Compacta

El CPU, la memoria, las fuentes de alimentación y las Entradas/Salidas (E/S) residen en un solo bloque monolítico. Es común en modelos de gama baja o antiguos. Aquí, el mapa de memoria suele ser estático y limitado.

#### 2. Estructura Modular (El Reto Interesante)

Este diseño divide el sistema en módulos específicos (CPU, CP de comunicación, E/S digitales/analógicas) montados sobre un carril DIN o un RACK (bastidor), unidos por un bus externo.

**El Dato Crítico para el Mapa de Memoria**:
En los sistemas S5 que analizamos, descubrí que la dirección de memoria de un módulo de Entrada/Salida (E/S) no se configura por software, sino que depende físicamente de su ranura (slot) en el rack.
* Ranura 0 --> Mapeada al Byte 0 de E/S.
* Ranura 1 --> Mapeada al Byte 1 de E/S.
* Ranura 2 --> Mapeada al Byte 2 de E/S.

<img src="/img/devlog-plc/post-11.png" alt="Diagrama memoria S5" width="800" height="400" />

Esto significa que el mapa de memoria (Address Space) está físicamente ligado a la configuración del hardware. Si un atacante quiere manipular la "Válvula de Presión" ubicada en la salida A 2.0, necesita saber que esa tarjeta está físicamente en la Ranura 2.

### Limitaciones del Hardware Legado

Trabajar con el S5-95U implicó lidiar con limitaciones severas que hoy parecen impensables:

* **Memoria de usuario**: Apenas 16KB a 64KB.
* **Puerto de programación**: Interfaz AS511 (Serial Loop Current), que requiere cables y convertidores específicos, nada de USB o Ethernet directo.
* **Volatilidad**: Programas almacenados en EPROM o RAM respaldada por batería. Si la batería falla, el programa muere.

Esta "arqueología" fue necesaria para entender la base sobre la que se construyó el S7 moderno. Muchas de las idiosincrasias del direccionamiento de memoria en S7 (como las áreas de Periferia PE/PA) son herencia directa de esta lógica de slots del S5.

### AWL: Más que un Lenguaje de Listado de Instrucciones

La mayor revelación de esta fase de investigación fue desmitificar el lenguaje AWL (Anweisungsliste, o STL en inglés). A menudo despreciado por los programadores modernos que prefieren lenguajes gráficos (LAD/FUP), AWL es, en esencia, el Lenguaje Ensamblador de la arquitectura Siemens.

Al analizar los binarios compilados y su ejecución, noté que AWL opera bajo una arquitectura de Acumulador, muy similar a procesadores simples de 8 o 16 bits.

<img src="/img/devlog-plc/post-6.jpg" alt="Entorno de emulación PG-2000 simulando la estructura de hardware S5" width="800" height="400" />

### Anatomía de la Instrucción y Opcodes
Una instrucción AWL no es abstracta; se traduce directamente a Opcodes de máquina. Durante el análisis de volcados de memoria, identifiqué patrones claros:

- **Carga (L - Load)**: Equivalente a `MOV EAX, [dir]`. Carga datos en el AKKU1 (Acumulador 1).
	- Opcode S7: 0xFB

- **Transferencia (T - Transfer)**: Equivalente a `MOV [dir]`, EAX. Mueve datos del AKKU1 a memoria.
	- Opcode S7: 0x7E

<img src="/img/devlog-plc/post-7.jpg" alt="Desensamblado manual mostrando Opcodes 0xFB y 0x7E" width="800" height="400" />

### El registro Status Word

Al igual que en x86 tenemos el registro EFLAGS, los PLCs Siemens poseen el Status Word. Entender estos bits es la diferencia entre escribir un programa que funciona y escribir un exploit que controla el flujo de ejecución.

He mapeado los bits más críticos de este registro:

| Bit       | Nombre   | Descripción Técnica   | Equivalente en x86    |
| --------  | -------- | --------------------- | --------------------- |
| 0         | FC       | Indica si la instrucción actual es la primera de una cadena lógica. Si es 0, se inicia una nueva secuencia lógica. Si es 1, se combina con la lógica anterior.		 			   | N/A 				   |
| 1         | RLO      | Es el acumulador de operaciones booleanas. Almacena el resultado de la última operación lógica o de comparación bit a bit. 					   | ZF/CF 				   |
| 2         | STA      | Muestra el estado de la dirección de memoria (operando) consultada en la instrucción actual (independientemente de la lógica). 					   | N/A 				   |
| 3         | OR       | Se utiliza para combinar operaciones lógicas AND antes de una operación OR (lógica de paréntesis o ramas paralelas). 					   | N/A 				   |
| 4         | OS       | Bit de desbordamiento "almacenado". Si ocurre un OV, el OS se pone en 1 y se queda así hasta que se resetee explícitamente o se cambie de bloque.		 			   | N/A 				   |
| 5         | OV       | Indica que ocurrió un error matemático (desbordamiento, división por cero) en la última operación ejecutada.		 			   | OF					   |
| 6         | CC1      | Junto con CC0, define el resultado de comparaciones matemáticas o instrucciones de carga/transferencia. 					   | SF/ZF				   |
| 7         | CC0      | Se evalúa junto con CC1. (Ej: CC1=0, CC0=0 significa que el resultado fue 0).		 			   | SF/ZF				   |
| 8         | BR       | Transfiere el resultado de la palabra de estado a la lógica binaria. Es vital para el mecanismo ENO (Enable Output). 					   | EAX 				   | 


### Estructuras de Datos: Temporizadores y Contadores

En el análisis de malware industrial (como Stuxnet), manipular los tiempos es un vector de ataque común (ej. alterar frecuencias de motores). Siemens maneja estructuras de memoria específicas para esto.

### Temporizadores (Timers)

El formato de tiempo en S5 es KT n.x (donde n es valor y x es base de tiempo). Existen 5 tipos fundamentales que residen en áreas de memoria reservadas:

* **S_EVERZ (SE)**: Retardo a la conexión. (Solo activa si la entrada dura > tiempo).
* **S_SEVERZ (SS)**: Retardo con memoria (Latch).
* **S_IMPULS (SI)**: Pulso estricto (depende de la entrada).
* **S_PULS (SP)**: Pulso fijo.
* **S_AVERZ (SA)**: Retardo a la desconexión.

### Contadores 
Operan en un rango de 0-999. Una vulnerabilidad potencial en lógica mal diseñada es el desbordamiento o underflow de contadores si se usan para control de bucles (loops), aunque el hardware limita los valores extremos.

Comprender estas estructuras a nivel de bit nos permite buscar "huecos" en la memoria del sistema para inyectar datos o manipular el estado del proceso sin tocar el código principal.

### La Máquina Virtual MC7

Quizás el hallazgo más importante para el investigador de seguridad es este: En los PLCs modernos Siemens, el código que escribes NO se ejecuta directamente en el procesador.

La arquitectura funciona en tres capas:

* **Capa Lógica (Usuario)**: Código AWL/SCL/LAD.
* **Capa Intermedia (Bytecode)**: El código se compila a MC7, un bytecode propietario de Siemens.
* **Capa Física (Hardware)**: Un procesador (generalmente ARM, MIPS o un ASIC propietario) que interpreta o compila JIT (Just-In-Time) el MC7.

Esto significa que cuando hacemos ingeniería inversa a un binario de S7, estamos analizando una Máquina Virtual. Esto explica por qué el set de instrucciones MC7 parece "ajeno" al hardware físico real del dispositivo.

<img src="/img/devlog-plc/post-4.jpg" alt="Diagrama de flujo: AWL -> Bytecode MC7 -> Ejecución en CPU Nativa" width="800" height="400" />

### Cambios Críticos en la Organización de Memoria
| Característica       | Siemens S5      | Siemens S7            				| 
| -------------------  | --------------- | ------------------------------------ | 
| Ancho de palabra     | 16-bits         | 32-bits               				|
| Acumuladores         | 2 (AKKU1-AKKU2) | 2 o 4 (ACU1-ACU4)      				|
| Datos Locales        | No existe       | Stack Local ('L') 	                |
| Bloques de Datos     | DB, DX	         | DB Globales y DB de Instancia (DI)   |

### Bloques de Datos (DB)

En S5, los datos se almacenaban de forma plana (DW 0, DW 1...). En S7, el direccionamiento se vuelve orientado a Bytes (DBB, DBW, DBD).

Una diferencia clave es el DB de Instancia. Mientras que un DB global es accesible por cualquiera, un DI está atado a una llamada de función específica (FB). Esto crea un encapsulamiento que, si bien mejora la programación, obliga al atacante a entender el contexto de ejecución para inyectar datos exitosamente sin corromper el proceso.

<img src="/img/devlog-plc/post-3.jpg" alt="Comparativa de Hexdump vs Visualización en WinSPS" width="800" height="400" />

El análisis estático de estos bloques (como se ve en la imagen superior con herramientas como Rizin o hexdumps crudos) revela que el formato del archivo .wld (World) que es el resultado de intentar exportar el formato compilado en WinSPS. 

### Direccionamiento Indirecto

Para inyectar código o manipular memoria de forma arbitraria en un sistema industrial, no podemos depender de direcciones estáticas (M 10.0, A 4.0). Las direcciones cambian, los programas se reasignan. Para lograr una explotación fiable, necesitamos Punteros.

Aquí es donde la diferencia entre S5 y S7 se vuelve un abismo.

#### S5: Direccionamiento Indirecto Primitivo

En el sistema S5, el direccionamiento indirecto se lograba utilizando la propia memoria como un mecanismo de puntero rudimentario. Se cargaba un índice (un número) en una palabra de memoria y luego se instruía al procesador para que operara sobre el recurso especificado por ese índice.
El siguiente ejemplo ilustra este concepto:

```asm
L KB 5      ; Carga la constante 5 en el acumulador.
T MW 2      ; Transfiere el contenido del acumulador (el valor 5) 
			; 	a la palabra de memoria MW 2.
B MW 2      ; La instrucción 'B' se usa para realizar llamadas incondicionales.
L T  0      ; Carga el Temporizador T(MW2) -> T5.
```

Lo que podemos observar es que, aunque inicialmente cargamos el valor literal "5" en la memoria MW 2, la línea L T 0 interpreta el contenido de MW 2 como el número del temporizador. Al ejecutar esa instrucción, el sistema entiende que debe cargar el Temporizador 5 (T5), no el valor 5.
De esta manera, si cambiamos el valor almacenado en la palabra de memoria MW 2 (por ejemplo, a 2), podremos "apuntar" o direccionar indirectamente a otro temporizador (el Temporizador 2).

#### S7: Registros de Dirección (AR1 / AR2)

S7 introdujo registros de 32 bits dedicados para punteros: AR1 y AR2. Esto permite aritmética de punteros real, esencial para recorrer memoria (memory scraping) o calcular offsets para inyecciones.

El formato del puntero S7 es complejo: P#Byte.Bit.

**Escenario de Explotación Teórico (Lectura/Escritura Arbitraria)**:
Imaginemos que queremos leer una entrada física y copiarla a una zona de memoria que controlamos, pero no sabemos la dirección exacta en tiempo de compilación.
```asm
L   P#8.0       ; Carga un puntero literal a la dirección 8.0.
T   MD 2        ; Guárdalo en la marca de memoria MD 2.
; --- Aritmética de punteros posible aquí ---
L   EB [MD 2]   ; Carga el Byte de Entrada apuntado dinámicamente por MD 2 (EB 8)
T   MW [MD 2]   ; Escribe en la Palabra de Marcas apuntada por MD 2
```

Si un atacante puede controlar el valor de MD 2 (por ejemplo, a través de una entrada HMI no saneada o un paquete Modbus), puede redirigir las lecturas y escrituras del PLC a cualquier zona de la memoria (incluyendo áreas de sistema o Periferia), logrando una primitiva de Lectura/Escritura Arbitraria.

#### Vectores de Entrada: Protocolos e Infraestructura
Ningún PLC es una isla. El código malicioso necesita una vía de entrada.

* **Modbus TCP**: El "Telnet" de los protocolos industriales. Texto claro, sin autenticación. Si tienes conectividad IP, puedes escribir directamente en los registros de memoria (Holding Registers) usando funciones estándar (FC06/FC16). Es el vector más ruidoso pero efectivo.
	<img src="/img/devlog-plc/post-5.png" alt="Diagrama Modbus TCP" width="800" height="400" />

* **S7comm / Profinet**: Protocolos propietarios de Siemens. Profinet transporta tráfico en tiempo real sobre Ethernet. S7comm (puerto 102) maneja la carga y descarga de bloques de código. Herramientas como Snap7 permiten interactuar a este nivel.
	<img src="/img/devlog-plc/post-8.png" alt="Diagrama S7comm" width="800" height="600" />

* **DNP3 / ICCP**: Usados en subestaciones eléctricas. Complejos pero críticos.
	<img src="/img/devlog-plc/post-9.png" alt="Diagrama DNP3" width="800" height="600" />

#### Conclusión
Esta investigación de tres meses ha confirmado varias hipótesis:
* La seguridad por oscuridad es una falacia: AWL es reversible, y el bytecode MC7, aunque no documentado oficialmente, sigue patrones lógicos predecibles.
* La virtualización es la clave: Los PLCs modernos son computadoras corriendo una VM. Escapar de esa VM (VM Escape) hacia el OS nativo es el "Santo Grial" de la explotación de ICS modernos (como se vio en Triton o Pipedream).
* Los fundamentos no cambian: A pesar de la complejidad del S7, los conceptos de registros, flags de estado y punteros heredados del S5 siguen vigentes bajo el capó.

Eventualmente, pienso migrar mi laboratorio hacia el Fuzzing del protocolo S7comm para encontrar fallos en el manejo de paquetes malformados que permitan Denegación de Servicio (DoS) o ejecución de código remota.

Sin embargo, por ahora encuentro varias limitaciones principalmente al no tener equipos fisicos para las pruebas. 