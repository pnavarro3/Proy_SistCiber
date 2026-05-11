import socket
import time
import random
import threading
from pathlib import Path
from pyniryo import NiryoRobot, PinID, PinState
from VisionRobot import procesar_tablero_3x3_azules
from Ned2_ULL import backup_robot_pose, restore_robot_pose

BACKUP_FILE = Path(__file__).resolve().parent.parent / "config" / "posbackup.json"

# ─── Configuración TCP/IP ─────────────────────────────────────
HOST = "10.209.2.130"
PORT = 5000

HOST2 = "10.209.2.167"
PORT2 = 6000

# ─── Constantes del juego ─────────────────────────────────────
POSICIONES_TABLERO = [1, 2, 3, 4, 5, 6, 7, 8, 9]
COMBINACIONES_GANADORAS = [
    {1, 2, 3}, {4, 5, 6}, {7, 8, 9},
    {1, 4, 7}, {2, 5, 8}, {3, 6, 9},
    {1, 5, 9}, {3, 5, 7},
]
MAX_TURNOS = 30


# ═══════════════════════════════════════════════════════════════
#  Comunicación TCP/IP
# ═══════════════════════════════════════════════════════════════

def enviar_mensaje(sock: socket.socket, mensaje: str) -> None:
    data = (mensaje + "\n").encode("utf-8")
    sock.sendall(data)
    hex_str = " ".join(f"0x{b:02X}" for b in data)
    print(f"[TX] '{mensaje}' | HEX: {hex_str}")


def recibir_mensaje(sock: socket.socket) -> str:
    data = sock.recv(1024)
    if not data:
        print("[RX] Conexión cerrada.")
        return ""
    mensaje = data.decode("utf-8")
    print(f"[RX] '{mensaje.strip()}'")
    return mensaje


# ─── Hilo para segunda conexión ────────────────────────────────

def escuchar_sock2(sock2):
    while True:
        try:
            data = sock2.recv(1024)
            if not data:
                print("[SOCK2] Conexión cerrada.")
                break

            mensaje = data.decode("utf-8")
            print(f"[SOCK2 RX RAW] '{mensaje.strip()}'")

        except Exception as e:
            print(f"[SOCK2 ERROR] {e}")
            break


# ═══════════════════════════════════════════════════════════════
#  Movimiento del robot
# ═══════════════════════════════════════════════════════════════

def nombre_pose(posicion):
    if posicion.startswith("alm"):
        return posicion
    return f"pos{posicion}"


def nombre_aprox(posicion):
    if posicion.startswith("alm"):
        return "aproxalm"
    return f"aprox{posicion}"


def mover_ficha(robot, origen, destino):
    aprox_orig = nombre_aprox(origen)
    pose_orig  = nombre_pose(origen)
    aprox_dest = nombre_aprox(destino)
    pose_dest  = nombre_pose(destino)

    robot.clear_collision_detected()

    robot.move(robot.get_pose_saved(aprox_orig))
    time.sleep(1)

    robot.move(robot.get_pose_saved(pose_orig))
    time.sleep(1)

    robot.grasp_with_tool()
    time.sleep(0.5)

    robot.move(robot.get_pose_saved(aprox_orig))
    time.sleep(1)

    robot.move(robot.get_pose_saved(aprox_dest))
    time.sleep(1)

    robot.move(robot.get_pose_saved(pose_dest))
    time.sleep(1)

    robot.release_with_tool()
    time.sleep(0.5)

    robot.move(robot.get_pose_saved(aprox_dest))
    time.sleep(1)

    robot.move(robot.get_pose_saved("vista_gen"))
    time.sleep(1)


# ═══════════════════════════════════════════════════════════════
#  Lógica del juego
# ═══════════════════════════════════════════════════════════════

def verificar_victoria(posiciones):
    s = set(posiciones)
    return any(combo.issubset(s) for combo in COMBINACIONES_GANADORAS)


def casillas_libres(propias, rival):
    ocupadas = set(propias) | set(rival)
    return [c for c in POSICIONES_TABLERO if c not in ocupadas]


def construir_act(fichas_propias, fichas_rival):
    tablero = ['_'] * 9
    for pos in fichas_rival:
        tablero[pos - 1] = 'X'
    for pos in fichas_propias:
        tablero[pos - 1] = 'O'
    return f"ACT {''.join(tablero)}"


# ═══════════════════════════════════════════════════════════════
#  IA
# ═══════════════════════════════════════════════════════════════

def decidir_jugada(fichas_propias, fichas_rival):
    libres = casillas_libres(fichas_propias, fichas_rival)

    if len(fichas_propias) < 3:
        origen = f"alm{len(fichas_propias)+1}"
        if len(fichas_propias) == 0 and 5 in libres:
            return origen, "5"
        return origen, str(random.choice(libres))

    origen = str(random.choice(fichas_propias))
    destino = str(random.choice(libres))
    return origen, destino


# ═══════════════════════════════════════════════════════════════
#  Turno rival
# ═══════════════════════════════════════════════════════════════

def esperar_turno_rival(robot):
    while True:
        if robot.digital_read("DI1") == PinState.HIGH:
            while robot.digital_read("DI1") == PinState.HIGH:
                time.sleep(0.05)
            return
        time.sleep(0.01)


def detectar_fichas_rival(robot):
    return procesar_tablero_3x3_azules(robot)


# ═══════════════════════════════════════════════════════════════
#  Partida
# ═══════════════════════════════════════════════════════════════

def partida(robot, sock, sock2=None):
    print("Esperando INI...")
    modo = None

    while modo is None:
        msg = recibir_mensaje(sock)
        partes = msg.split()
        if len(partes) >= 2 and partes[0] == "INI":
            modo = partes[1].upper()

    fichas_propias = []
    fichas_rival = []
    almacen = ["alm1", "alm2", "alm3"]

    while True:
        if modo == "AUT":
            origen, destino = decidir_jugada(fichas_propias, fichas_rival)
            enviar_mensaje(sock, "DEC")

        else:
            msg = recibir_mensaje(sock)
            partes = msg.split()
            origen, destino = partes[1], partes[2]

        mover_ficha(robot, origen, destino)

        if sock2:
            enviar_mensaje(sock2, f"MOV {origen} {destino}")

        enviar_mensaje(sock, "FTJ")

        if origen.startswith("alm"):
            almacen.remove(origen)
            fichas_propias.append(int(destino))
        else:
            fichas_propias.remove(int(origen))
            fichas_propias.append(int(destino))

        esperar_turno_rival(robot)
        fichas_rival = detectar_fichas_rival(robot)

        enviar_mensaje(sock, construir_act(fichas_propias, fichas_rival))
        enviar_mensaje(sock, "FTU")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    robot = NiryoRobot("10.10.10.10")
    robot.calibrate_auto()
    robot.update_tool()
    robot.set_arm_max_velocity(50)

    restore_robot_pose(robot, BACKUP_FILE)
    robot.move(robot.get_pose_saved("vista_gen"))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print("Conectado a servidor principal")

    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock2.connect((HOST2, PORT2))
        print("Conectado a servidor secundario")

        hilo = threading.Thread(target=escuchar_sock2, args=(sock2,), daemon=True)
        hilo.start()

    except:
        print("No se pudo conectar a la segunda conexión")
        sock2 = None

    try:
        partida(robot, sock, sock2)

    finally:
        sock.close()
        if sock2:
            sock2.close()
        backup_robot_pose(robot, BACKUP_FILE)
        robot.close_connection()


if __name__ == "__main__":
    main()