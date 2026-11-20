"""Módulo 7 – Modo distribuido (cliente / servidor por sockets TCP).

Protocolo: un mensaje JSON por línea (terminado en '\\n').
  {"tipo": "REGISTRAR", "proceso": {"nombre": "PX", "llegada": 0, "rafaga": 5}}
  {"tipo": "CONSULTAR"}                 -> estado de la cola de procesos
  {"tipo": "PLANIFICAR", "quantum": 3}  -> el servidor planifica la cola con RR
  {"tipo": "PING"}
El servidor atiende varios clientes a la vez: un hilo por conexión (mejora) y un
Lock protege la cola compartida.
"""
import json
import socket
import threading
import time
from . import cpu
from .utils import titulo, pedir_entero, pausa

HOST_DEFECTO, PUERTO_DEFECTO = "127.0.0.1", 5050
TIMEOUT = 3  # segundos


class ServidorSimOS:
    def __init__(self, host="0.0.0.0", puerto=PUERTO_DEFECTO, verbose=True):
        self.host, self.puerto, self.verbose = host, puerto, verbose
        self.cola = []                         # procesos registrados [(nombre, llegada, rafaga)]
        self.lock = threading.Lock()
        self.sock = None
        self.activo = False
        self.hilo = None

    def log(self, msg):
        if self.verbose:
            print(f"   [SERVIDOR] {msg}", flush=True)

    # ---- ciclo de vida
    def iniciar(self, en_segundo_plano=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.puerto))
        self.sock.listen(5)
        self.sock.settimeout(0.5)              # para poder revisar self.activo y detenerlo
        self.activo = True
        self.log(f"Escuchando en {self.host}:{self.puerto}")
        if en_segundo_plano:
            self.hilo = threading.Thread(target=self._aceptar, daemon=True)
            self.hilo.start()
        else:
            self._aceptar()

    def detener(self):
        self.activo = False
        if self.hilo:
            self.hilo.join(timeout=2)
        if self.sock:
            self.sock.close()
        self.log("Servidor detenido")

    def _aceptar(self):
        while self.activo:
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._atender, args=(conn, addr), daemon=True).start()

    # ---- atención de un cliente
    def _atender(self, conn, addr):
        with conn:
            conn.settimeout(TIMEOUT)
            archivo = conn.makefile("r", encoding="utf-8")
            for linea in archivo:
                try:
                    respuesta = self._procesar(json.loads(linea))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                    respuesta = {"ok": False, "error": f"Mensaje inválido: {e}"}
                self.log(f"{addr[0]}:{addr[1]} -> {respuesta.get('mensaje', respuesta.get('error', 'ok'))}")
                conn.sendall((json.dumps(respuesta, ensure_ascii=False) + "\n").encode("utf-8"))

    def _procesar(self, msg):
        tipo = msg.get("tipo")
        if tipo == "PING":
            return {"ok": True, "mensaje": "PONG"}
        if tipo == "REGISTRAR":
            p = msg["proceso"]
            proc = (str(p["nombre"]), int(p["llegada"]), int(p["rafaga"]))
            if proc[1] < 0 or proc[2] <= 0:
                raise ValueError("llegada >= 0 y ráfaga > 0")
            with self.lock:
                if any(x[0] == proc[0] for x in self.cola):
                    return {"ok": False, "error": f"Ya existe un proceso llamado {proc[0]}"}
                self.cola.append(proc)
                n = len(self.cola)
            return {"ok": True, "mensaje": f"Proceso {proc[0]} registrado ({n} en cola)"}
        if tipo == "CONSULTAR":
            with self.lock:
                cola = [{"nombre": n, "llegada": l, "rafaga": r} for n, l, r in self.cola]
            return {"ok": True, "mensaje": f"Cola con {len(cola)} procesos", "cola": cola}
        if tipo == "PLANIFICAR":
            q = int(msg.get("quantum", 3))
            with self.lock:
                procs = list(self.cola)
            if not procs:
                return {"ok": False, "error": "La cola está vacía"}
            gantt = cpu.round_robin(procs, q)
            _, pe, pr = cpu.metricas(procs, gantt)
            return {"ok": True, "mensaje": f"Planificado con RR q={q}",
                    "gantt": cpu.gantt_texto(gantt), "espera_promedio": round(pe, 2),
                    "retorno_promedio": round(pr, 2)}
        return {"ok": False, "error": f"Tipo de mensaje desconocido: {tipo}"}


# ---------------------------------------------------------------- cliente
def enviar(mensaje, host=HOST_DEFECTO, puerto=PUERTO_DEFECTO):
    """Envía un mensaje y devuelve la respuesta. Nunca lanza excepción: si el
    servidor no responde devuelve {"ok": False, "error": ...} con un mensaje claro."""
    try:
        with socket.create_connection((host, puerto), timeout=TIMEOUT) as s:
            s.sendall((json.dumps(mensaje) + "\n").encode("utf-8"))
            datos = s.makefile("r", encoding="utf-8").readline()
            if not datos:
                return {"ok": False, "error": "El servidor cerró la conexión sin responder."}
            return json.loads(datos)
    except ConnectionRefusedError:
        return {"ok": False, "error": f"No se pudo conectar a {host}:{puerto}: el servidor no está "
                                      "en ejecución o rechazó la conexión."}
    except socket.timeout:
        return {"ok": False, "error": f"Tiempo de espera agotado ({TIMEOUT} s): el servidor no responde."}
    except OSError as e:
        return {"ok": False, "error": f"Error de red: {e}"}


def mostrar_respuesta(r):
    if not r.get("ok"):
        print(f"  ✘ ERROR: {r.get('error')}")
        return
    print(f"  ✔ {r.get('mensaje')}")
    if "cola" in r:
        for p in r["cola"]:
            print(f"     - {p['nombre']}: llegada={p['llegada']} ráfaga={p['rafaga']}")
    if "gantt" in r:
        print(r["gantt"])
        print(f"     Espera promedio = {r['espera_promedio']} | Retorno promedio = {r['retorno_promedio']}")


def caso_prueba(puerto=PUERTO_DEFECTO + 1):
    """Caso oficial: registrar un proceso, consultar la cola y apagar el servidor."""
    srv = ServidorSimOS("127.0.0.1", puerto)
    srv.iniciar()
    for n, l, r in cpu.CASO_PRUEBA:                 # el servidor ya tiene la cola del módulo 1
        srv.cola.append((n, l, r))
    print("\n[CLIENTE] 1) Registrar proceso nuevo P6 (llegada 7, ráfaga 3)")
    mostrar_respuesta(enviar({"tipo": "REGISTRAR",
                              "proceso": {"nombre": "P6", "llegada": 7, "rafaga": 3}}, puerto=puerto))
    print("\n[CLIENTE] 2) Consultar la cola de procesos")
    mostrar_respuesta(enviar({"tipo": "CONSULTAR"}, puerto=puerto))
    print("\n[CLIENTE] 3) Pedir al servidor que planifique con RR q=3")
    mostrar_respuesta(enviar({"tipo": "PLANIFICAR", "quantum": 3}, puerto=puerto))
    print("\n[ADMIN] 4) Se apaga el servidor...")
    srv.detener()
    time.sleep(0.3)
    print("\n[CLIENTE] 5) Consultar la cola con el servidor apagado")
    mostrar_respuesta(enviar({"tipo": "CONSULTAR"}, puerto=puerto))
    print("\nEl cliente sigue funcionando: el error se manejó sin cerrar el programa.")


_servidor_actual = None


def menu():
    global _servidor_actual
    host, puerto = HOST_DEFECTO, PUERTO_DEFECTO
    while True:
        titulo("MÓDULO 7 – MODO DISTRIBUIDO (CLIENTE / SERVIDOR)")
        estado = f"ACTIVO en puerto {_servidor_actual.puerto}" if _servidor_actual else "detenido"
        print(f"Servidor local: {estado} | Cliente apunta a {host}:{puerto}")
        print("1. Iniciar servidor en segundo plano")
        print("2. Iniciar servidor en primer plano (Ctrl+C para detener)")
        print("3. Detener servidor")
        print("4. Configurar host/puerto del cliente")
        print("5. Cliente: registrar proceso")
        print("6. Cliente: consultar cola")
        print("7. Cliente: planificar cola (RR)")
        print("8. Caso de prueba oficial automático")
        print("0. Volver")
        op = input("Opción: ").strip()
        try:
            if op in ("1", "2"):
                if _servidor_actual:
                    print("Ya hay un servidor activo.")
                else:
                    p = pedir_entero("Puerto", 1024, 65535, PUERTO_DEFECTO)
                    srv = ServidorSimOS("0.0.0.0", p)
                    if op == "1":
                        srv.iniciar(True)
                        _servidor_actual = srv
                    else:
                        try:
                            srv.iniciar(False)
                        except KeyboardInterrupt:
                            srv.detener()
            elif op == "3":
                if _servidor_actual:
                    _servidor_actual.detener()
                    _servidor_actual = None
                else:
                    print("No hay servidor activo.")
            elif op == "4":
                host = input(f"Host [{host}]: ").strip() or host
                puerto = pedir_entero("Puerto", 1024, 65535, puerto)
            elif op == "5":
                nombre = input("Nombre del proceso: ").strip() or "PX"
                mostrar_respuesta(enviar({"tipo": "REGISTRAR", "proceso": {
                    "nombre": nombre, "llegada": pedir_entero("Llegada", 0),
                    "rafaga": pedir_entero("Ráfaga", 1)}}, host, puerto))
            elif op == "6":
                mostrar_respuesta(enviar({"tipo": "CONSULTAR"}, host, puerto))
            elif op == "7":
                mostrar_respuesta(enviar({"tipo": "PLANIFICAR",
                                          "quantum": pedir_entero("Quantum", 1, defecto=3)}, host, puerto))
            elif op == "8":
                caso_prueba()
            elif op == "0":
                return
            else:
                continue
        except OSError as e:
            print(f"No se pudo iniciar el servidor: {e}")
        pausa()
