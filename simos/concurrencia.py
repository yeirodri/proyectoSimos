"""Módulo 2 – Concurrencia y sincronización.

1) Contador compartido sin sincronización vs. con mutex (threading.Lock).
2) Productor–consumidor con buffer acotado usando semáforos (threading.Semaphore).
3) Mejora opcional: interbloqueo (deadlock) y su prevención ordenando los recursos.

Nota técnica (Python): el GIL hace que 'x += 1' rara vez muestre la condición de
carrera. Para que el problema sea visible y repetible separamos la operación en
LEER -> (cambio de contexto) -> ESCRIBIR, forzando el cambio con time.sleep(0),
que es exactamente lo que el planificador del SO puede hacer en cualquier momento.
"""
import threading
import time
import random
from collections import deque
from .utils import titulo, pedir_entero, pausa

_impresion = threading.Lock()   # para que las líneas de distintos hilos no se mezclen


def log(msg):
    with _impresion:
        print(msg, flush=True)


# ---------------------------------------------------------------- 1. contador
class Contador:
    def __init__(self):
        self.valor = 0
        self.lock = threading.Lock()


def _incrementar_sin_lock(c, veces):
    for _ in range(veces):
        leido = c.valor          # 1. leer
        time.sleep(0)            # 2. posible cambio de contexto (sección crítica expuesta)
        c.valor = leido + 1      # 3. escribir -> puede sobrescribir el trabajo de otro hilo


def _incrementar_con_lock(c, veces):
    for _ in range(veces):
        with c.lock:             # solo un hilo a la vez dentro de la sección crítica
            leido = c.valor
            time.sleep(0)
            c.valor = leido + 1


def contador_compartido(n_hilos=10, veces=1000):
    esperado = n_hilos * veces
    resultados = {}
    for etiqueta, funcion in (("SIN sincronización", _incrementar_sin_lock),
                              ("CON mutex (Lock)", _incrementar_con_lock)):
        c = Contador()
        hilos = [threading.Thread(target=funcion, args=(c, veces), name=f"H{i + 1}")
                 for i in range(n_hilos)]
        inicio = time.perf_counter()
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        dur = time.perf_counter() - inicio
        perdidos = esperado - c.valor
        resultados[etiqueta] = c.valor
        print(f"{etiqueta:<20} -> resultado = {c.valor:>6} | esperado = {esperado} | "
              f"actualizaciones perdidas = {perdidos} | {dur:.2f} s")
    print("\nConclusión: sin mutex varios hilos leen el mismo valor y se pisan "
          "(condición de carrera);\ncon mutex la sección crítica es atómica y el resultado es correcto.")
    return resultados


# ---------------------------------------------------------------- 2. productor-consumidor
def productor_consumidor(tam_buffer=5, total=20, n_prod=2, n_cons=2, retardo=0.02):
    buffer = deque()
    mutex = threading.Lock()                     # exclusión mutua sobre el buffer
    vacios = threading.Semaphore(tam_buffer)     # espacios libres
    llenos = threading.Semaphore(0)              # elementos disponibles
    producidos, consumidos = [], []

    # Repartir los elementos entre productores y consumidores
    cuota_p = [total // n_prod + (1 if i < total % n_prod else 0) for i in range(n_prod)]
    cuota_c = [total // n_cons + (1 if i < total % n_cons else 0) for i in range(n_cons)]
    siguiente = iter(range(1, total + 1))
    gen_lock = threading.Lock()

    def productor(cuota):
        for _ in range(cuota):
            with gen_lock:
                item = next(siguiente)
            time.sleep(random.uniform(0, retardo))   # "fabricar" el elemento
            vacios.acquire()                         # espera si el buffer está lleno
            with mutex:
                buffer.append(item)
                producidos.append(item)
                log(f"[{threading.current_thread().name}] produce {item:>2}  "
                    f"buffer={list(buffer)} ({len(buffer)}/{tam_buffer})")
            llenos.release()

    def consumidor(cuota):
        for _ in range(cuota):
            llenos.acquire()                         # espera si el buffer está vacío
            with mutex:
                item = buffer.popleft()
                consumidos.append(item)
                log(f"    [{threading.current_thread().name}] consume {item:>2}  "
                    f"buffer={list(buffer)} ({len(buffer)}/{tam_buffer})")
            vacios.release()
            time.sleep(random.uniform(0, retardo * 1.5))   # "usar" el elemento

    hilos = [threading.Thread(target=productor, args=(cuota_p[i],), name=f"Productor-{i + 1}")
             for i in range(n_prod)]
    hilos += [threading.Thread(target=consumidor, args=(cuota_c[i],), name=f"Consumidor-{i + 1}")
              for i in range(n_cons)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    ok = sorted(consumidos) == list(range(1, total + 1)) and not buffer
    print(f"\nProducidos: {len(producidos)} | Consumidos: {len(consumidos)} | "
          f"Buffer final: {list(buffer)} | Correcto: {'SÍ' if ok else 'NO'}")
    return ok


# ---------------------------------------------------------------- 3. interbloqueo (mejora)
def interbloqueo():
    r1, r2 = threading.Lock(), threading.Lock()
    nombres = {id(r1): "R1", id(r2): "R2"}

    def tomar(proc, primero, segundo, bloqueados):
        with primero:
            log(f"  {proc} obtiene {nombres[id(primero)]}")
            time.sleep(0.2)                       # da tiempo a que el otro tome su recurso
            log(f"  {proc} solicita {nombres[id(segundo)]}...")
            if segundo.acquire(timeout=1.5):      # timeout solo para poder detectar el deadlock
                log(f"  {proc} obtiene {nombres[id(segundo)]} y termina su trabajo")
                segundo.release()
            else:
                bloqueados.append(proc)
                log(f"  {proc} NO pudo obtener {nombres[id(segundo)]} (esperando indefinidamente)")

    print("\n>> Escenario A: P1 pide R1→R2 y P2 pide R2→R1 (espera circular)")
    bloq = []
    hs = [threading.Thread(target=tomar, args=("P1", r1, r2, bloq)),
          threading.Thread(target=tomar, args=("P2", r2, r1, bloq))]
    [h.start() for h in hs]
    [h.join() for h in hs]
    print("   Resultado: " + ("INTERBLOQUEO detectado (espera circular). Sin el timeout de "
          f"{', '.join(bloq)} ambos procesos quedarían esperando para siempre." if bloq else "sin interbloqueo"))

    print("\n>> Escenario B: prevención – ambos piden los recursos en el MISMO orden (R1→R2)")
    bloq = []
    hs = [threading.Thread(target=tomar, args=("P1", r1, r2, bloq)),
          threading.Thread(target=tomar, args=("P2", r1, r2, bloq))]
    [h.start() for h in hs]
    [h.join() for h in hs]
    print(f"   Resultado: {'INTERBLOQUEO' if bloq else 'sin interbloqueo: se rompe la condición de espera circular'}")


def menu():
    while True:
        titulo("MÓDULO 2 – CONCURRENCIA Y SINCRONIZACIÓN")
        print("1. Contador compartido (caso de prueba: 10 hilos x 1.000)")
        print("2. Productor–consumidor (caso de prueba: buffer 5, 20 elementos)")
        print("3. Contador / productor–consumidor con datos propios")
        print("4. Interbloqueo y prevención (mejora opcional)")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "1":
            contador_compartido(10, 1000)
        elif op == "2":
            productor_consumidor(5, 20)
        elif op == "3":
            contador_compartido(pedir_entero("Hilos", 1, 100, 10), pedir_entero("Incrementos por hilo", 1, defecto=1000))
            productor_consumidor(pedir_entero("Tamaño del buffer", 1, defecto=5),
                                 pedir_entero("Total de elementos", 1, defecto=20),
                                 pedir_entero("Productores", 1, 10, 2),
                                 pedir_entero("Consumidores", 1, 10, 2))
        elif op == "4":
            interbloqueo()
        elif op == "0":
            return
        else:
            continue
        pausa()
