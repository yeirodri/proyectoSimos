"""Módulo 4 – Almacenamiento: planificación de disco FCFS, SSTF, SCAN y C-SCAN (mejora).

Cada algoritmo devuelve el recorrido completo del cabezal (incluye la posición
inicial y, en SCAN/C-SCAN, los extremos del disco que toca). El desplazamiento
total es la suma de |posición_i - posición_(i-1)|.
"""
from .utils import titulo, pedir_entero, pedir_lista_enteros, tabla, pausa

COLA_PRUEBA = [130, 25, 160, 45, 90, 10, 185, 75]
CABEZAL_PRUEBA, MIN_PRUEBA, MAX_PRUEBA = 70, 0, 199


def fcfs(cabezal, cola, **_):
    return [cabezal] + list(cola)


def sstf(cabezal, cola, **_):
    """Shortest Seek Time First: atiende la solicitud más cercana al cabezal."""
    pendientes, recorrido, pos = list(cola), [cabezal], cabezal
    while pendientes:
        # empate de distancia: se prefiere el cilindro menor (criterio fijo y documentado)
        sig = min(pendientes, key=lambda c: (abs(c - pos), c))
        pendientes.remove(sig)
        recorrido.append(sig)
        pos = sig
    return recorrido


def scan(cabezal, cola, minimo, maximo, hacia_mayores=True):
    """Ascensor: avanza en una dirección hasta el extremo y luego se devuelve."""
    mayores = sorted(c for c in cola if c >= cabezal)
    menores = sorted((c for c in cola if c < cabezal), reverse=True)
    if hacia_mayores:
        ida = mayores + ([maximo] if menores and (not mayores or mayores[-1] != maximo) else [])
        return [cabezal] + ida + menores
    ida = menores + ([minimo] if mayores and (not menores or menores[-1] != minimo) else [])
    return [cabezal] + ida + mayores


def cscan(cabezal, cola, minimo, maximo, hacia_mayores=True):
    """Circular SCAN: recorre hasta el extremo, salta al extremo opuesto y sigue en la misma dirección.
    El salto de retorno SÍ se cuenta en el desplazamiento (convención más común en los textos)."""
    mayores = sorted(c for c in cola if c >= cabezal)
    menores = sorted(c for c in cola if c < cabezal)
    if hacia_mayores:
        if not menores:
            return [cabezal] + mayores
        return [cabezal] + mayores + [maximo, minimo] + menores
    if not mayores:
        return [cabezal] + menores[::-1]
    return [cabezal] + menores[::-1] + [minimo, maximo] + mayores[::-1]


ALGORITMOS = {"FCFS": fcfs, "SSTF": sstf, "SCAN": scan, "C-SCAN": cscan}


def desplazamiento(recorrido):
    return sum(abs(b - a) for a, b in zip(recorrido, recorrido[1:]))


def comparar(cabezal, cola, minimo, maximo, hacia_mayores=True):
    print(f"Cabezal en {cabezal}, cilindros {minimo}-{maximo}, dirección "
          f"{'hacia mayores' if hacia_mayores else 'hacia menores'}")
    print(f"Cola de solicitudes: {cola}")
    resultados, filas = {}, []
    for nombre, alg in ALGORITMOS.items():
        rec = alg(cabezal, cola, minimo=minimo, maximo=maximo, hacia_mayores=hacia_mayores)
        total = desplazamiento(rec)
        resultados[nombre] = total
        pasos = " + ".join(str(abs(b - a)) for a, b in zip(rec, rec[1:]))
        print(f"\n--- {nombre} ---")
        print("Orden de atención: " + " → ".join(map(str, rec)))
        print(f"Desplazamiento: {pasos} = {total} cilindros")
        filas.append((nombre, total, f"{total / len(cola):.2f}"))
    print()
    tabla(["Algoritmo", "Desplazamiento total", "Promedio por solicitud"], filas)
    mejor = min(resultados, key=resultados.get)
    print(f">>> Mejor algoritmo: {mejor} ({resultados[mejor]} cilindros)")
    return resultados


def menu():
    while True:
        titulo("MÓDULO 4 – ALMACENAMIENTO (PLANIFICACIÓN DE DISCO)")
        print("1. Caso de prueba oficial (cabezal 70, 0-199, hacia mayores)")
        print("2. Ingresar datos propios")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "1":
            comparar(CABEZAL_PRUEBA, COLA_PRUEBA, MIN_PRUEBA, MAX_PRUEBA, True)
        elif op == "2":
            mn = pedir_entero("Cilindro mínimo", 0, defecto=0)
            mx = pedir_entero("Cilindro máximo", mn + 1, defecto=199)
            cab = pedir_entero("Posición inicial del cabezal", mn, mx, 70)
            cola = pedir_lista_enteros("Cola de solicitudes", COLA_PRUEBA)
            if any(c < mn or c > mx for c in cola):
                print("Hay solicitudes fuera del rango de cilindros.")
            else:
                dir_ = input("Dirección inicial (M = mayores / m = menores) [M]: ").strip()
                comparar(cab, cola, mn, mx, dir_ != "m")
        elif op == "0":
            return
        else:
            continue
        pausa()
