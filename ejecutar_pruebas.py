"""Ejecuta TODOS los casos de prueba obligatorios (sección 4) sin menú interactivo.
Útil para el informe, la tabla comparativa y como respaldo en la sustentación:
    python ejecutar_pruebas.py            -> todos
    python ejecutar_pruebas.py 1 2        -> solo módulos 1 y 2
"""
import sys
from simos import cpu, concurrencia, memoria, disco, seguridad, entrada_salida, distribuido
from simos.utils import titulo


def m1():
    titulo("CASO DE PRUEBA – MÓDULO 1: PLANIFICACIÓN DE CPU")
    print("Procesos (llegada, ráfaga): " + ", ".join(f"{n}({l},{r})" for n, l, r in cpu.CASO_PRUEBA))
    cpu.comparar(cpu.CASO_PRUEBA, cpu.QUANTUM_PRUEBA)
    print("\n--- Mejora: recomendación de quantum ---")
    cpu.recomendar_quantum(cpu.CASO_PRUEBA)


def m2():
    titulo("CASO DE PRUEBA – MÓDULO 2: CONCURRENCIA")
    print(">> Contador compartido: 10 hilos x 1.000 incrementos (esperado 10.000)\n")
    concurrencia.contador_compartido(10, 1000)
    print("\n>> Productor–consumidor: buffer de 5 posiciones, 20 elementos, 2 productores y 2 consumidores\n")
    concurrencia.productor_consumidor(5, 20)
    print("\n>> Mejora: interbloqueo y prevención")
    concurrencia.interbloqueo()


def m3():
    titulo("CASO DE PRUEBA – MÓDULO 3: MEMORIA")
    print("Cadena:", ", ".join(map(str, memoria.CADENA_PRUEBA)))
    for m in (3, 4):
        memoria.comparar(memoria.CADENA_PRUEBA, m)


def m4():
    titulo("CASO DE PRUEBA – MÓDULO 4: ALMACENAMIENTO")
    disco.comparar(disco.CABEZAL_PRUEBA, disco.COLA_PRUEBA, disco.MIN_PRUEBA, disco.MAX_PRUEBA, True)


def m5():
    titulo("CASO DE PRUEBA – MÓDULO 5: SEGURIDAD")
    ok, rol = seguridad.autenticar("ana", "ana123")
    print(f"Login de 'ana': {'correcto' if ok else 'fallido'} -> rol {rol}")
    permitido = seguridad.verificar_acceso("ana", rol, 5)
    print(f"'ana' ({rol}) intenta entrar al módulo 5 -> {'PERMITIDO' if permitido else 'DENEGADO'}")
    print("\nMatriz de acceso:")
    seguridad.mostrar_matriz()
    print()
    seguridad.ver_bitacora(5)


def m6():
    titulo("CASO DE PRUEBA – MÓDULO 6: ENTRADA/SALIDA")
    entrada_salida.simular_impresora(entrada_salida.TRABAJOS_PRUEBA)
    print("\n>> Mejora: caché de lectura")
    entrada_salida.simular_cache(entrada_salida.LECTURAS_PRUEBA, 3)


def m7():
    titulo("CASO DE PRUEBA – MÓDULO 7: MODO DISTRIBUIDO")
    distribuido.caso_prueba()


CASOS = {"1": m1, "2": m2, "3": m3, "4": m4, "5": m5, "6": m6, "7": m7}

if __name__ == "__main__":
    for k in (sys.argv[1:] or CASOS):
        CASOS[k]()
