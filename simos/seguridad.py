"""Módulo 5 – Seguridad y protección.

- Autenticación con usuarios y roles (Administrador / Usuario).
- Contraseñas guardadas como hash SHA-256 con sal aleatoria (mejora opcional).
- Bloqueo del usuario tras 3 intentos fallidos (mejora opcional).
- Matriz de acceso rol x módulo: los accesos sin permiso se bloquean.
- Bitácora de auditoría en texto: fecha, hora, usuario, acción, PERMITIDO/DENEGADO.
"""
import hashlib
import json
import os
import secrets
from datetime import datetime
from getpass import getpass
from .utils import titulo, tabla, pausa

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
ARCHIVO_USUARIOS = os.path.join(BASE, "usuarios.json")
ARCHIVO_BITACORA = os.path.join(BASE, "bitacora.txt")
MAX_INTENTOS = 3

MODULOS = {
    1: "Planificación de CPU",
    2: "Concurrencia y sincronización",
    3: "Gestión de memoria",
    4: "Almacenamiento",
    5: "Usuarios, permisos y bitácora",
    6: "Entrada/salida",
    7: "Modo distribuido",
}

# Matriz de acceso: rol -> conjunto de módulos permitidos
MATRIZ_ACCESO = {
    "Administrador": {1, 2, 3, 4, 5, 6, 7},
    "Usuario": {1, 2, 3, 4, 6},
}

USUARIOS_INICIALES = [            # (usuario, contraseña inicial, rol)
    ("admin", "admin123", "Administrador"),
    ("ana", "ana123", "Usuario"),
    ("luis", "luis123", "Usuario"),
]


# ---------------------------------------------------------------- hash y persistencia
def hash_password(password, sal):
    return hashlib.sha256((sal + password).encode("utf-8")).hexdigest()


def _cargar():
    if not os.path.exists(ARCHIVO_USUARIOS):
        _crear_usuarios_iniciales()
    with open(ARCHIVO_USUARIOS, encoding="utf-8") as f:
        return json.load(f)


def _guardar(usuarios):
    os.makedirs(BASE, exist_ok=True)
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


def _crear_usuarios_iniciales():
    usuarios = {}
    for nombre, pwd, rol in USUARIOS_INICIALES:
        sal = secrets.token_hex(8)
        usuarios[nombre] = {"sal": sal, "hash": hash_password(pwd, sal), "rol": rol,
                            "intentos": 0, "bloqueado": False}
    _guardar(usuarios)


def registrar(usuario, accion, permitido):
    """Escribe una línea en la bitácora de auditoría."""
    os.makedirs(BASE, exist_ok=True)
    ahora = datetime.now()
    linea = (f"{ahora:%Y-%m-%d} | {ahora:%H:%M:%S} | {usuario:<10} | {accion:<52} | "
             f"{'PERMITIDO' if permitido else 'DENEGADO'}\n")
    with open(ARCHIVO_BITACORA, "a", encoding="utf-8") as f:
        f.write(linea)


# ---------------------------------------------------------------- autenticación y control de acceso
def autenticar(usuario, password):
    """Devuelve (ok, rol_o_mensaje)."""
    usuarios = _cargar()
    u = usuarios.get(usuario)
    if u is None:
        registrar(usuario or "?", "Inicio de sesión (usuario inexistente)", False)
        return False, "Usuario o contraseña incorrectos."
    if u["bloqueado"]:
        registrar(usuario, "Inicio de sesión (cuenta bloqueada)", False)
        return False, "Cuenta bloqueada por intentos fallidos. Contacte al administrador."
    if secrets.compare_digest(hash_password(password, u["sal"]), u["hash"]):
        u["intentos"] = 0
        _guardar(usuarios)
        registrar(usuario, "Inicio de sesión", True)
        return True, u["rol"]
    u["intentos"] += 1
    if u["intentos"] >= MAX_INTENTOS:
        u["bloqueado"] = True
        msg = f"Contraseña incorrecta. La cuenta quedó BLOQUEADA tras {MAX_INTENTOS} intentos."
        registrar(usuario, f"Bloqueo de cuenta ({MAX_INTENTOS} intentos fallidos)", False)
    else:
        msg = f"Usuario o contraseña incorrectos. Intentos restantes: {MAX_INTENTOS - u['intentos']}"
        registrar(usuario, "Inicio de sesión (contraseña incorrecta)", False)
    _guardar(usuarios)
    return False, msg


def tiene_permiso(rol, modulo):
    return modulo in MATRIZ_ACCESO.get(rol, set())


def verificar_acceso(usuario, rol, modulo):
    """Consulta la matriz, registra el intento en la bitácora y devuelve True/False."""
    permitido = tiene_permiso(rol, modulo)
    registrar(usuario, f"Acceso al módulo {modulo} ({MODULOS[modulo]})", permitido)
    return permitido


def login():
    titulo("SimOS v1.0 – INICIO DE SESIÓN")
    while True:
        usuario = input("Usuario: ").strip()
        try:
            password = getpass("Contraseña: ")
        except (EOFError, KeyboardInterrupt):
            return None, None
        ok, info = autenticar(usuario, password)
        if ok:
            return usuario, info
        print(f"  {info}")
        if input("¿Intentar de nuevo? (s/n) [s]: ").strip().lower() == "n":
            return None, None


# ---------------------------------------------------------------- menú del módulo 5 (solo admin)
def mostrar_matriz():
    roles = list(MATRIZ_ACCESO)
    filas = [(f"{m}. {n}", *("✔" if m in MATRIZ_ACCESO[r] else "✘" for r in roles))
             for m, n in MODULOS.items()]
    tabla(["Módulo"] + roles, filas)


def ver_bitacora(ultimas=20):
    if not os.path.exists(ARCHIVO_BITACORA):
        print("La bitácora está vacía.")
        return
    with open(ARCHIVO_BITACORA, encoding="utf-8") as f:
        lineas = f.readlines()
    print(f"Últimos {min(ultimas, len(lineas))} de {len(lineas)} registros:")
    print("FECHA      | HORA     | USUARIO    | ACCIÓN" + " " * 46 + " | RESULTADO")
    for l in lineas[-ultimas:]:
        print(l.rstrip())


def listar_usuarios():
    usuarios = _cargar()
    tabla(["Usuario", "Rol", "Intentos fallidos", "Estado", "Hash SHA-256 (inicio)"],
          [(n, u["rol"], u["intentos"], "BLOQUEADO" if u["bloqueado"] else "Activo", u["hash"][:16] + "…")
           for n, u in usuarios.items()])


def crear_usuario(admin):
    usuarios = _cargar()
    nombre = input("Nuevo usuario: ").strip()
    if not nombre or nombre in usuarios:
        print("Nombre vacío o ya existe.")
        return
    rol = input(f"Rol {list(MATRIZ_ACCESO)} [Usuario]: ").strip() or "Usuario"
    if rol not in MATRIZ_ACCESO:
        print("Rol inválido.")
        return
    pwd = getpass("Contraseña: ")
    if len(pwd) < 6:
        print("La contraseña debe tener al menos 6 caracteres.")
        return
    sal = secrets.token_hex(8)
    usuarios[nombre] = {"sal": sal, "hash": hash_password(pwd, sal), "rol": rol,
                        "intentos": 0, "bloqueado": False}
    _guardar(usuarios)
    registrar(admin, f"Creó el usuario {nombre} ({rol})", True)
    print("Usuario creado.")


def desbloquear(admin):
    usuarios = _cargar()
    nombre = input("Usuario a desbloquear: ").strip()
    if nombre in usuarios:
        usuarios[nombre]["bloqueado"] = False
        usuarios[nombre]["intentos"] = 0
        _guardar(usuarios)
        registrar(admin, f"Desbloqueó al usuario {nombre}", True)
        print("Usuario desbloqueado.")
    else:
        print("No existe.")


def menu(usuario):
    while True:
        titulo("MÓDULO 5 – USUARIOS, PERMISOS Y BITÁCORA")
        print("1. Ver matriz de acceso")
        print("2. Ver bitácora de auditoría")
        print("3. Listar usuarios")
        print("4. Crear usuario")
        print("5. Desbloquear usuario")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "1":
            mostrar_matriz()
        elif op == "2":
            ver_bitacora()
        elif op == "3":
            listar_usuarios()
        elif op == "4":
            crear_usuario(usuario)
        elif op == "5":
            desbloquear(usuario)
        elif op == "0":
            return
        else:
            continue
        pausa()
