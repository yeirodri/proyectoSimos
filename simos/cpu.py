"""Módulo 1 – Planificación de CPU: FCFS, Round Robin y SJF (mejora opcional).

Cada algoritmo recibe una lista de procesos [(nombre, llegada, rafaga)] y devuelve
el diagrama de Gantt como lista de tramos (nombre, inicio, fin). Con el Gantt se
calculan tiempo de finalización, retorno (fin - llegada) y espera (retorno - ráfaga).
"""
from collections import deque
from .utils import titulo, pedir_entero, tabla, pausa

CASO_PRUEBA = [("P1", 0, 8), ("P2", 1, 4), ("P3", 2, 9), ("P4", 3, 5), ("P5", 6, 2)]
QUANTUM_PRUEBA = 3


# ---------------------------------------------------------------- algoritmos
def fcfs(procesos):
    """First Come First Served: se atiende en orden de llegada, sin expropiación."""
    gantt, t = [], 0
    for nombre, llegada, rafaga in sorted(procesos, key=lambda p: p[1]):
        if t < llegada:                       # CPU ociosa hasta que llegue el proceso
            gantt.append(("--", t, llegada))
            t = llegada
        gantt.append((nombre, t, t + rafaga))
        t += rafaga
    return gantt


def round_robin(procesos, quantum):
    """Round Robin: cada proceso usa la CPU como máximo "quantum" unidades.

    Convención: si un proceso llega en el mismo instante en que otro es
    expropiado, el que llega entra a la cola ANTES que el expropiado.
    """
    pendientes = sorted(procesos, key=lambda p: p[1])
    restante = {p[0]: p[2] for p in procesos}
    cola, gantt, t, i = deque(), [], 0, 0

    def admitir_llegadas(hasta):
        nonlocal i
        while i < len(pendientes) and pendientes[i][1] <= hasta:
            cola.append(pendientes[i][0])
            i += 1

    admitir_llegadas(t)
    while cola or i < len(pendientes):
        if not cola:                          # CPU ociosa: saltar a la próxima llegada
            siguiente = pendientes[i][1]
            gantt.append(("--", t, siguiente))
            t = siguiente
            admitir_llegadas(t)
            continue
        actual = cola.popleft()
        uso = min(quantum, restante[actual])
        gantt.append((actual, t, t + uso))
        t += uso
        restante[actual] -= uso
        admitir_llegadas(t)                   # primero los que llegaron durante el quantum
        if restante[actual] > 0:
            cola.append(actual)               # luego vuelve el expropiado al final
    return _unir_tramos(gantt)


def sjf(procesos):
    """Shortest Job First (no expropiativo): entre los que ya llegaron, la ráfaga más corta."""
    pendientes = list(procesos)
    gantt, t = [], 0
    while pendientes:
        listos = [p for p in pendientes if p[1] <= t]
        if not listos:
            proxima = min(p[1] for p in pendientes)
            gantt.append(("--", t, proxima))
            t = proxima
            continue
        elegido = min(listos, key=lambda p: (p[2], p[1]))   # empate: el que llegó primero
        gantt.append((elegido[0], t, t + elegido[2]))
        t += elegido[2]
        pendientes.remove(elegido)
    return gantt


def _unir_tramos(gantt):
    """Une tramos consecutivos del mismo proceso (ej. P2 0-3 y P2 3-4 -> P2 0-4)."""
    unido = []
    for tramo in gantt:
        if unido and unido[-1][0] == tramo[0] and unido[-1][2] == tramo[1]:
            unido[-1] = (tramo[0], unido[-1][1], tramo[2])
        else:
            unido.append(tramo)
    return unido


# ---------------------------------------------------------------- métricas
def metricas(procesos, gantt):
    """Devuelve filas (nombre, llegada, ráfaga, fin, retorno, espera) y la espera promedio."""
    filas = []
    for nombre, llegada, rafaga in procesos:
        fin = max(f for n, _, f in gantt if n == nombre)
        retorno = fin - llegada
        espera = retorno - rafaga
        filas.append((nombre, llegada, rafaga, fin, retorno, espera))
    prom_espera = sum(f[5] for f in filas) / len(filas)
    prom_retorno = sum(f[4] for f in filas) / len(filas)
    return filas, prom_espera, prom_retorno


def gantt_texto(gantt):
    """Diagrama de Gantt en texto: |  P1  |  P2  | con los tiempos debajo."""
    barra, tiempos = "|", str(gantt[0][1])
    for nombre, ini, fin in gantt:
        ancho = max(len(nombre) + 2, (fin - ini) * 2)
        barra += nombre.center(ancho) + "|"
        tiempos += str(fin).rjust(ancho + 1)
    return barra + "\n" + tiempos


def mostrar_resultado(nombre_alg, procesos, gantt):
    print(f"\n--- {nombre_alg} ---")
    print(gantt_texto(gantt))
    filas, pe, pr = metricas(procesos, gantt)
    tabla(["Proceso", "Llegada", "Ráfaga", "Finalización", "Retorno", "Espera"], filas)
    print(f"Tiempo promedio de espera: {pe:.2f}   |   Retorno promedio: {pr:.2f}")
    return pe


def comparar(procesos, quantum, incluir_sjf=True):
    resultados = {
        "FCFS": mostrar_resultado("FCFS", procesos, fcfs(procesos)),
        f"Round Robin (q={quantum})": mostrar_resultado(
            f"Round Robin (quantum = {quantum})", procesos, round_robin(procesos, quantum)),
    }
    if incluir_sjf:
        resultados["SJF"] = mostrar_resultado("SJF no expropiativo (mejora)", procesos, sjf(procesos))
    print("\n>>> Resumen de espera promedio")
    tabla(["Algoritmo", "Espera promedio"], [(k, f"{v:.2f}") for k, v in resultados.items()])
    mejor = min(resultados, key=resultados.get)
    print(f">>> Mejor algoritmo para este caso: {mejor} ({resultados[mejor]:.2f})")
    return resultados


def recomendar_quantum(procesos, q_min=1, q_max=10):
    """Mejora opcional: prueba varios quantum y recomienda el de menor espera promedio."""
    filas = []
    for q in range(q_min, q_max + 1):
        _, pe, _ = metricas(procesos, round_robin(procesos, q))
        filas.append((q, round(pe, 2)))
    tabla(["Quantum", "Espera promedio"], filas)
    mejor = min(filas, key=lambda f: (f[1], f[0]))
    print(f">>> Quantum recomendado: {mejor[0]} (espera promedio {mejor[1]:.2f})")
    return mejor[0]


# ---------------------------------------------------------------- entrada de datos
def leer_procesos_teclado():
    n = pedir_entero("Número de procesos", 1, 50)
    procesos = []
    for k in range(n):
        print(f"Proceso {k + 1}:")
        nombre = input("  Nombre: ").strip() or f"P{k + 1}"
        llegada = pedir_entero("  Tiempo de llegada", 0)
        rafaga = pedir_entero("  Ráfaga de CPU", 1)
        procesos.append((nombre, llegada, rafaga))
    return procesos


def leer_procesos_archivo(ruta):
    """Formato del archivo: una línea por proceso -> nombre,llegada,rafaga (# = comentario)."""
    procesos = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            nombre, llegada, rafaga = [x.strip() for x in linea.split(",")]
            procesos.append((nombre, int(llegada), int(rafaga)))
    return procesos


def menu():
    while True:
        titulo("MÓDULO 1 – PLANIFICACIÓN DE CPU")
        print("1. Ejecutar caso de prueba oficial (RR q=3)")
        print("2. Ingresar procesos por teclado")
        print("3. Cargar procesos desde archivo")
        print("4. Recomendar quantum (mejora opcional)")
        print("0. Volver")
        op = input("Opción: ").strip()
        try:
            if op == "1":
                comparar(CASO_PRUEBA, QUANTUM_PRUEBA)
            elif op == "2":
                procs = leer_procesos_teclado()
                comparar(procs, pedir_entero("Quantum", 1, defecto=3))
            elif op == "3":
                ruta = input("Ruta del archivo [datos/procesos.txt]: ").strip() or "datos/procesos.txt"
                procs = leer_procesos_archivo(ruta)
                comparar(procs, pedir_entero("Quantum", 1, defecto=3))
            elif op == "4":
                recomendar_quantum(CASO_PRUEBA)
            elif op == "0":
                return
            else:
                continue
        except (OSError, ValueError) as e:
            print(f"Error leyendo datos: {e}")
        pausa()
