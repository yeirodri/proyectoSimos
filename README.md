# SimOS v1.0 – Simulador de un sistema operativo

Proyecto final de **Sistemas Operativos** (Ingeniería de Sistemas, VI semestre).
SimOS simula, en consola, cómo un sistema operativo administra los recursos de un computador:
CPU, concurrencia, memoria, disco, seguridad, entrada/salida y comunicación en red.

## Integrantes

| Integrante | Módulos |
|---|---|
| Yeiler Alvarez | M1 CPU · M4 Almacenamiento · M5 Seguridad · M7 Distribuido |
| José David Caedenas | M2 Concurrencia · M6 Entrada/salida |
| Nicol Sareth Segovia | M3 Memoria · integración del menú principal |

Docente: Andrés Camilo Peláez Vanegas.

## Requisitos

- Python **3.8 o superior** (probado con 3.13). No requiere librerías externas:
  solo la biblioteca estándar (`threading`, `socket`, `hashlib`, `json`).
- Windows, Linux o macOS.

## Instalación y ejecución

```bash
git clone https://github.com/yeirodri/proyectoSimos.git
cd proyectoSimos
python main.py            # en Linux/macOS puede ser python3
```

Usuarios iniciales (las contraseñas se guardan como hash SHA-256 con sal en `datos/usuarios.json`,
que se crea en la primera ejecución):

| Usuario | Contraseña | Rol           | Módulos permitidos |
|---------|------------|---------------|--------------------|
| admin   | admin123   | Administrador | 1–7                |
| ana     | ana123     | Usuario       | 1, 2, 3, 4, 6      |
| luis    | luis123    | Usuario       | 1, 2, 3, 4, 6      |

> Tras 3 contraseñas incorrectas la cuenta se bloquea; el administrador la desbloquea desde el módulo 5.
> Para volver al estado inicial borre `datos/usuarios.json` y `datos/bitacora.txt`.

### Ejecutar todos los casos de prueba (sin menú)

```bash
python ejecutar_pruebas.py          # los 7 módulos
python ejecutar_pruebas.py 1 2      # solo los módulos 1 y 2
```

### Modo distribuido en dos terminales / dos computadores

1. Terminal A (servidor): `python main.py` → `admin` → opción 7 → opción 2 (servidor en primer plano, puerto 5050).
2. Terminal B (cliente): `python main.py` → `admin` → opción 7 → opción 4 (IP del servidor) → opciones 5, 6 y 7.
3. Si el servidor está en otro equipo, abra el puerto 5050 en su firewall.

## Estructura

```
SimOS/
├── main.py                  # login + menú principal + control de acceso
├── ejecutar_pruebas.py      # corre los casos de prueba de la sección 4
├── simos/
│   ├── cpu.py               # M1: FCFS, Round Robin, SJF*, recomendación de quantum*
│   ├── concurrencia.py      # M2: contador con/sin mutex, productor–consumidor, interbloqueo*
│   ├── memoria.py           # M3: FIFO, LRU, OPT*, gráfica de fallos*
│   ├── disco.py             # M4: FCFS, SSTF, SCAN, C-SCAN*
│   ├── seguridad.py         # M5: login, roles, matriz de acceso, bitácora, SHA-256*, bloqueo*
│   ├── entrada_salida.py    # M6: spooling de impresora, estados Listo/Bloqueado, caché*
│   ├── distribuido.py       # M7: servidor/cliente TCP (JSON), multicliente con hilos*
│   └── utils.py             # entrada validada y tablas de texto
└── datos/
    ├── procesos.txt         # procesos de prueba para cargar desde archivo (M1)
    ├── usuarios.json        # (se genera) usuarios con hash
    └── bitacora.txt         # (se genera) auditoría
```
`*` = mejora opcional.

## Resultados esperados de los casos de prueba

| Módulo | Resultado |
|--------|-----------|
| 1. CPU | Espera promedio: FCFS 11,00 · RR(q=3) 14,20 · SJF 7,80 |
| 2. Concurrencia | Sin mutex < 10.000 (varía) · con mutex = 10.000 · productor–consumidor 20/20 |
| 3. Memoria | 3 marcos: FIFO 15, LRU 12, OPT 9 · 4 marcos: FIFO 10, LRU 8, OPT 8 |
| 4. Disco | FCFS 825 · SSTF 290 · SCAN 318 · C-SCAN 373 cilindros |
| 5. Seguridad | `ana` (Usuario) → módulo 5 = DENEGADO y registrado en bitácora |
| 6. E/S | Orden P1→P2→P3, esperas 0, 3, 4 (promedio 2,33) |
| 7. Distribuido | Registro y consulta OK; con el servidor apagado el cliente muestra error y sigue |

## Uso de inteligencia artificial

Se usó un asistente de IA (Claude) como apoyo para proponer la estructura modular y un primer
borrador del código. El grupo revisó, probó y ajustó cada módulo y debe poder explicarlo en la sustentación.
