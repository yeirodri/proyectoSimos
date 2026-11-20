"""Módulo 3 – Gestión de memoria: paginación con reemplazo FIFO, LRU y OPT (mejora).

Cada algoritmo devuelve la lista de pasos: (página, marcos_después, fallo?, víctima).
"""
from collections import deque
from .utils import titulo, pedir_entero, pedir_lista_enteros, pausa

CADENA_PRUEBA = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]


def fifo(cadena, n_marcos):
    """Reemplaza la página que lleva más tiempo cargada en memoria."""
    marcos = [None] * n_marcos
    orden_carga = deque()                       # índices de marco en orden de llegada
    pasos = []
    for pag in cadena:
        victima = None
        fallo = pag not in marcos
        if fallo:
            if None in marcos:                  # hay marco libre
                idx = marcos.index(None)
            else:
                idx = orden_carga.popleft()     # el más antiguo
                victima = marcos[idx]
            marcos[idx] = pag
            orden_carga.append(idx)
        pasos.append((pag, list(marcos), fallo, victima))
    return pasos


def lru(cadena, n_marcos):
    """Reemplaza la página usada hace más tiempo (Least Recently Used)."""
    marcos = [None] * n_marcos
    ultimo_uso = {}
    pasos = []
    for t, pag in enumerate(cadena):
        victima = None
        fallo = pag not in marcos
        if fallo:
            if None in marcos:
                idx = marcos.index(None)
            else:
                idx = min(range(n_marcos), key=lambda i: ultimo_uso[marcos[i]])
                victima = marcos[idx]
            marcos[idx] = pag
        ultimo_uso[pag] = t
        pasos.append((pag, list(marcos), fallo, victima))
    return pasos


def optimo(cadena, n_marcos):
    """OPT: reemplaza la página que tardará más en volver a usarse (cota inferior teórica)."""
    marcos = [None] * n_marcos
    pasos = []
    for t, pag in enumerate(cadena):
        victima = None
        fallo = pag not in marcos
        if fallo:
            if None in marcos:
                idx = marcos.index(None)
            else:
                futuro = cadena[t + 1:]
                def proximo_uso(i):
                    return futuro.index(marcos[i]) if marcos[i] in futuro else float("inf")
                idx = max(range(n_marcos), key=proximo_uso)
                victima = marcos[idx]
            marcos[idx] = pag
        pasos.append((pag, list(marcos), fallo, victima))
    return pasos


ALGORITMOS = {"FIFO": fifo, "LRU": lru, "OPT": optimo}


def fallos(pasos):
    return sum(1 for p in pasos if p[2])


def mostrar_pasos(nombre, pasos, n_marcos):
    """Tabla vertical: cada columna es una referencia; F marca fallo de página."""
    print(f"\n--- {nombre} con {n_marcos} marcos ---")
    ancho = 3
    print("Ref.    " + "".join(str(p[0]).rjust(ancho) for p in pasos))
    print("        " + "-" * (ancho * len(pasos)))
    for m in range(n_marcos):
        fila = "".join((" " * ancho if p[1][m] is None else str(p[1][m]).rjust(ancho)) for p in pasos)
        print(f"Marco {m} {fila}")
    print("Fallo   " + "".join(("F" if p[2] else "").rjust(ancho) for p in pasos))
    total = fallos(pasos)
    print(f"Fallos de página: {total} de {len(pasos)} referencias "
          f"(tasa de fallos {total / len(pasos):.0%})")
    return total


def comparar(cadena, n_marcos, incluir_opt=True):
    resultados = {}
    for nombre, alg in ALGORITMOS.items():
        if nombre == "OPT" and not incluir_opt:
            continue
        resultados[nombre] = mostrar_pasos(nombre, alg(cadena, n_marcos), n_marcos)
    reales = {k: v for k, v in resultados.items() if k != "OPT"}
    mejor = min(reales, key=reales.get)
    print("\n>>> Resumen: " + " | ".join(f"{k}={v}" for k, v in resultados.items()))
    print(f">>> Entre FIFO y LRU, el de menos fallos fue: {mejor}"
          + (" (OPT es la referencia teórica, no implementable en la práctica)" if incluir_opt else ""))
    return resultados


def grafica_fallos(cadena, max_marcos=7):
    """Mejora opcional: 'gráfica' en texto de fallos según el número de marcos."""
    print("\nFallos de página según número de marcos")
    for m in range(1, max_marcos + 1):
        print(f"\nMarcos = {m}")
        for nombre, alg in ALGORITMOS.items():
            f = fallos(alg(cadena, m))
            print(f"  {nombre:<4} {'█' * f} {f}")


def menu():
    while True:
        titulo("MÓDULO 3 – GESTIÓN DE MEMORIA")
        print("1. Caso de prueba oficial (3 y 4 marcos)")
        print("2. Ingresar cadena de referencias y número de marcos")
        print("3. Gráfica de fallos vs. número de marcos (mejora)")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "1":
            for m in (3, 4):
                comparar(CADENA_PRUEBA, m)
        elif op == "2":
            cadena = pedir_lista_enteros("Cadena de referencias", CADENA_PRUEBA)
            comparar(cadena, pedir_entero("Número de marcos", 1, 20, 3))
        elif op == "3":
            grafica_fallos(pedir_lista_enteros("Cadena de referencias", CADENA_PRUEBA))
        elif op == "0":
            return
        else:
            continue
        pausa()
