"""Punto de entrada de SimOS: inicio de sesión + menú principal con control de acceso."""
import sys
from simos import seguridad, cpu, concurrencia, memoria, disco, entrada_salida, distribuido

MENUS = {
    1: cpu.menu,
    2: concurrencia.menu,
    3: memoria.menu,
    4: disco.menu,
    5: None,                 # el módulo 5 necesita el usuario actual (ver abajo)
    6: entrada_salida.menu,
    7: distribuido.menu,
}


def menu_principal(usuario, rol):
    while True:
        print("\n========== SimOS v1.0 ==========")
        print(f"Usuario: {usuario:<12} Rol: {rol}")
        print("--------------------------------")
        for num, nombre in seguridad.MODULOS.items():
            candado = "" if seguridad.tiene_permiso(rol, num) else "  [sin permiso]"
            print(f"{num}. {nombre}{candado}")
        print("0. Salir")
        op = input("Seleccione una opción: ").strip()
        if op == "0":
            seguridad.registrar(usuario, "Cierre de sesión", True)
            print("Sesión cerrada. ¡Hasta luego!")
            return
        if not op.isdigit() or int(op) not in MENUS:
            print("Opción inválida.")
            continue
        modulo = int(op)
        if not seguridad.verificar_acceso(usuario, rol, modulo):
            print(f"\n⛔ ACCESO DENEGADO: el rol '{rol}' no tiene permiso para el módulo "
                  f"{modulo} ({seguridad.MODULOS[modulo]}). El intento quedó en la bitácora.")
            continue
        if modulo == 5:
            seguridad.menu(usuario)
        else:
            MENUS[modulo]()


def main():
    usuario, rol = seguridad.login()
    if usuario:
        try:
            menu_principal(usuario, rol)
        except (KeyboardInterrupt, EOFError):
            seguridad.registrar(usuario, "Cierre de sesión (interrumpido)", True)
            print("\nSesión terminada.")
    else:
        print("No se inició sesión.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
