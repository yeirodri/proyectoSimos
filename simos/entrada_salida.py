"""Módulo 6 – Entrada/salida: impresora compartida con spooling y caché de lectura (mejora).

Simulación por tiempo discreto (tic = 1 unidad):
- Un proceso que envía un trabajo pasa de Listo -> Bloqueado (espera la E/S).
- El spooler toma los trabajos de la cola en orden FIFO y los imprime de uno en uno.
- Al terminar un trabajo se genera la "interrupción de fin de E/S" y el
  proceso dueño pasa de Bloqueado -> Listo.
"""
from collections import deque, OrderedDict
from .utils import titulo, pedir_entero, pedir_lista_enteros, tabla, pausa

# (proceso, instante en que envía el trabajo, duración de la impresión)
TRABAJOS_PRUEBA = [("P1", 0, 4), ("P2", 1, 2), ("P3", 2, 3)]


def simular_impresora(trabajos, verbose=True):
    pendientes = sorted(trabajos, key=lambda t: (t[1], t[0]))
    estado = {p: "Listo" for p, _, _ in trabajos}
    cola = deque()
    actual, fin_actual = None, None
    registro = {}            # proceso -> dict(llegada, duracion, inicio, fin)
    orden = []
    t = 0

    def mostrar(evento):
        if verbose:
            estados = "  ".join(f"{p}:{estado[p]:<9}" for p in sorted(estado))
            imp = f"imprimiendo {actual}" if actual else "libre"
            print(f"t={t:>2} | Impresora {imp:<15} | Cola spool {list(cola)!s:<14} | {estados} | {evento}")

    while pendientes or cola or actual:
        eventos = []
        # 1) ¿terminó el trabajo actual? -> interrupción de fin de E/S
        if actual and t == fin_actual:
            registro[actual]["fin"] = t
            estado[actual] = "Listo"
            eventos.append(f"INTERRUPCIÓN fin de E/S de {actual} -> Listo")
            actual = None
        # 2) llegada de nuevos trabajos al spool
        while pendientes and pendientes[0][1] == t:
            p, llegada, dur = pendientes.pop(0)
            cola.append(p)
            estado[p] = "Bloqueado"
            registro[p] = {"llegada": llegada, "duracion": dur}
            eventos.append(f"{p} envía trabajo ({dur} u.) -> Bloqueado")
        # 3) si la impresora está libre, el spooler toma el siguiente trabajo
        if actual is None and cola:
            actual = cola.popleft()
            registro[actual]["inicio"] = t
            fin_actual = t + registro[actual]["duracion"]
            orden.append(actual)
            eventos.append(f"Spooler envía a la impresora el trabajo de {actual}")
        mostrar("; ".join(eventos) if eventos else "-")
        if not (pendientes or cola or actual):
            break
        t += 1

    filas = []
    for p in orden:
        r = registro[p]
        filas.append((p, r["llegada"], r["duracion"], r["inicio"], r["fin"], r["inicio"] - r["llegada"]))
    print("\nOrden de atención: " + " → ".join(orden))
    tabla(["Proceso", "Envío", "Duración", "Inicio impresión", "Fin", "Espera en cola"], filas)
    prom = sum(f[5] for f in filas) / len(filas)
    print(f"Tiempo de espera promedio: {prom:.2f}")
    return orden, filas


# ---------------------------------------------------------------- mejora: caché de lectura
LECTURAS_PRUEBA = [1, 2, 3, 1, 4, 1, 2, 5, 1, 2, 3, 4, 5, 1, 2]


def simular_cache(lecturas, capacidad):
    """Caché LRU de bloques de disco: acierto si el bloque ya está en caché."""
    cache = OrderedDict()
    aciertos = 0
    print(f"Caché LRU de {capacidad} bloques")
    for b in lecturas:
        if b in cache:
            aciertos += 1
            cache.move_to_end(b)
            res = "ACIERTO"
        else:
            res = "fallo -> se lee del disco"
            if len(cache) >= capacidad:
                cache.popitem(last=False)
            cache[b] = True
        print(f"  lee bloque {b:>2}: {res:<26} caché={list(cache)}")
    tasa = aciertos / len(lecturas)
    print(f"Aciertos: {aciertos}/{len(lecturas)} -> tasa de aciertos = {tasa:.0%}")
    return tasa


def menu():
    while True:
        titulo("MÓDULO 6 – ENTRADA/SALIDA (COLA DE IMPRESIÓN)")
        print("1. Caso de prueba oficial (trabajos de 4, 2 y 3 u.)")
        print("2. Ingresar trabajos propios")
        print("3. Caché de lectura con tasa de aciertos (mejora)")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "1":
            simular_impresora(TRABAJOS_PRUEBA)
        elif op == "2":
            n = pedir_entero("Número de procesos", 1, 20)
            trabajos = []
            for i in range(n):
                trabajos.append((f"P{i + 1}", pedir_entero(f"  P{i + 1} instante de envío", 0),
                                 pedir_entero(f"  P{i + 1} duración", 1)))
            simular_impresora(trabajos)
        elif op == "3":
            simular_cache(pedir_lista_enteros("Bloques leídos", LECTURAS_PRUEBA),
                          pedir_entero("Capacidad de la caché", 1, defecto=3))
        elif op == "0":
            return
        else:
            continue
        pausa()
