"""Funciones de apoyo para la consola de SimOS (entrada de datos y tablas)."""


def titulo(texto):
    print("\n" + "=" * 60)
    print(texto.center(60))
    print("=" * 60)


def pedir_entero(msg, minimo=None, maximo=None, defecto=None):
    """Pide un entero validado. Enter vacío devuelve el valor por defecto."""
    while True:
        valor = input(f"{msg}" + (f" [{defecto}]" if defecto is not None else "") + ": ").strip()
        if valor == "" and defecto is not None:
            return defecto
        try:
            n = int(valor)
            if (minimo is not None and n < minimo) or (maximo is not None and n > maximo):
                raise ValueError
            return n
        except ValueError:
            rango = f" entre {minimo} y {maximo}" if minimo is not None and maximo is not None else ""
            print(f"  Valor inválido. Ingrese un número entero{rango}.")


def pedir_lista_enteros(msg, defecto=None):
    """Lee una lista separada por comas o espacios: '7, 0, 1, 2'."""
    while True:
        texto = input(f"{msg}" + (" [Enter = caso de prueba]" if defecto else "") + ": ").strip()
        if texto == "" and defecto:
            return list(defecto)
        try:
            return [int(x) for x in texto.replace(",", " ").split()]
        except ValueError:
            print("  Formato inválido. Ejemplo: 7, 0, 1, 2")


def tabla(encabezados, filas):
    """Imprime una tabla de texto alineada."""
    filas = [[str(c) for c in f] for f in filas]
    anchos = [max(len(str(h)), *(len(f[i]) for f in filas)) if filas else len(str(h))
              for i, h in enumerate(encabezados)]
    sep = "+" + "+".join("-" * (a + 2) for a in anchos) + "+"
    print(sep)
    print("| " + " | ".join(str(h).ljust(a) for h, a in zip(encabezados, anchos)) + " |")
    print(sep)
    for f in filas:
        print("| " + " | ".join(c.ljust(a) for c, a in zip(f, anchos)) + " |")
    print(sep)


def pausa():
    input("\nPresione Enter para continuar...")
