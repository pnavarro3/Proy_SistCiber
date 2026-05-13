import socket
import time
import random
import threading
import msvcrt
from pyniryo import NiryoRobot, PinID, PinState
from VisionRobot import procesar_tablero_3x3_azules
from Ned2_ULL import backup_robot_pose, restore_robot_pose

# ─── Configuración TCP/IP ─────────────────────────────────────
HOST = "10.209.2.125"
PORT = 5000

HOST2 = "10.209.2.72"
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
    print(f"[TX] '{mensaje}'")


def recibir_mensaje(sock: socket.socket) -> str:
    try:
        data = sock.recv(1024)
    except socket.timeout:
        return None
    if not data:
        print("[RX] Conexión cerrada.")
        return ""
    mensaje = data.decode("utf-8")
    if not mensaje.strip().startswith("MOV"):
        print(f"[RX] '{mensaje.strip()}'")
    return mensaje


# ─── Hilo para segunda conexión ────────────────────────────────

def escuchar_sock2(sock2):
    while True:
        try:
            msg = recibir_mensaje(sock2)
            if msg is None:
                continue
            if not msg:
                break
            print(f"[SOCK2 RX] {msg.strip()}")
        except:
            break


def esc_pulsado():
    if not msvcrt.kbhit():
        return False

    tecla = msvcrt.getch()
    if tecla in (b'\x00', b'\xe0') and msvcrt.kbhit():
        msvcrt.getch()
        return False

    if tecla == b'\x1b':
        print("[SYS] ESC pulsado. Finalizando...")
        return True

    return False


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

    robot.move(robot.get_pose_saved(pose_orig))

    robot.grasp_with_tool()

    robot.move(robot.get_pose_saved(aprox_orig))

    robot.move(robot.get_pose_saved(aprox_dest))

    robot.move(robot.get_pose_saved(pose_dest))

    robot.release_with_tool()

    robot.move(robot.get_pose_saved(aprox_dest))

    robot.move(robot.get_pose_saved("vista_gen"))


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

    movimientos = []
    if len(fichas_propias) < 3:
        origen_alm = f"alm{len(fichas_propias)+1}"
        for libre in libres:
            movimientos.append((origen_alm, str(libre)))
    else:
        for origen in fichas_propias:
            for libre in libres:
                movimientos.append((str(origen), str(libre)))

    # Regla principal: si existe jugada ganadora inmediata, tomarla siempre.
    for origen, destino in movimientos:
        if origen.startswith("alm"):
            nuevas_propias = list(fichas_propias)
            nuevas_propias.append(int(destino))
        else:
            nuevas_propias = [int(destino) if p == int(origen) else p for p in fichas_propias]

        if verificar_victoria(nuevas_propias):
            return origen, destino

    if not movimientos:
        return None, None

    if len(fichas_propias) < 3:
        if len(fichas_propias) == 0 and 5 in libres:
            return f"alm{len(fichas_propias)+1}", "5"

    return random.choice(movimientos)


# ═══════════════════════════════════════════════════════════════
#  Turno rival
# ═══════════════════════════════════════════════════════════════

def esperar_turno_rival(robot):
    while True:
        if esc_pulsado():
            return False
        if robot.digital_read("DI1") == PinState.HIGH:
            while robot.digital_read("DI1") == PinState.HIGH:
                if esc_pulsado():
                    return False
                time.sleep(0.05)
            return True
        time.sleep(0.01)


def detectar_fichas_rival(robot):
    return procesar_tablero_3x3_azules(robot)


# ═══════════════════════════════════════════════════════════════
#  Partida
# ═══════════════════════════════════════════════════════════════

def partida(robot, sock, sock2=None):
    while True:
        if esc_pulsado():
            return
        print("Esperando INI...")
        modo = None

        while modo is None:
            if esc_pulsado():
                return
            msg = recibir_mensaje(sock)
            if msg is None:
                continue
            if not msg:
                return
            partes = msg.split()
            if len(partes) >= 2 and partes[0].upper() == "INI":
                modo = partes[1].upper()
                print(f"Partida iniciada en modo {modo}")
                robot.say("Partida iniciada", 3)

        fichas_propias = []
        fichas_rival = []
        almacen = ["alm1", "alm2", "alm3"]
        turnos = 0

        while True:
            if esc_pulsado():
                return
            if modo == "AUT":
                origen, destino = decidir_jugada(fichas_propias, fichas_rival)
                if origen is None:
                    enviar_mensaje(sock, "FIN EMP")
                    robot.say("Empate", 3)
                    break
                enviar_mensaje(sock, "DEC")

            else:
                msg = recibir_mensaje(sock)
                if msg is None:
                    continue
                if not msg:
                    return
                partes = msg.split()
                if len(partes) < 3 or partes[0].upper() != "MOV":
                    continue
                origen, destino = partes[1], partes[2]

            mover_ficha(robot, origen, destino)

            if sock2:
                enviar_mensaje(sock2, f"MOV {origen} {destino}")

            enviar_mensaje(sock, "FTJ")
            robot.say("Te toca", 3)

            if origen.startswith("alm"):
                if origen in almacen:
                    almacen.remove(origen)
                fichas_propias.append(int(destino))
            else:
                fichas_propias.remove(int(origen))
                fichas_propias.append(int(destino))

            # ACT tras el turno del robot
            enviar_mensaje(sock, construir_act(fichas_propias, fichas_rival))

            if verificar_victoria(fichas_propias):
                enviar_mensaje(sock, "FIN VIC")
                robot.say("He ganado", 3)
                break

            if not casillas_libres(fichas_propias, fichas_rival):
                enviar_mensaje(sock, "FIN EMP")
                robot.say("Empate", 3)
                break

            if not esperar_turno_rival(robot):
                return
            fichas_rival = detectar_fichas_rival(robot)

            enviar_mensaje(sock, "FTU")
            # ACT al finalizar el turno del rival
            enviar_mensaje(sock, construir_act(fichas_propias, fichas_rival))

            if verificar_victoria(fichas_rival):
                enviar_mensaje(sock, "FIN DER")
                robot.say("Has ganado", 3)
                break

            if not casillas_libres(fichas_propias, fichas_rival):
                enviar_mensaje(sock, "FIN EMP")
                robot.say("Empate", 3)
                break

            turnos += 1
            if turnos >= MAX_TURNOS:
                enviar_mensaje(sock, "FIN EMP")
                robot.say("Empate", 3)
                break

        robot.move_to_home_pose()
        print("Partida finalizada. Esperando nueva orden INI...")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    robot = NiryoRobot("10.10.10.10")
    robot.calibrate_auto()
    robot.update_tool()
    robot.set_arm_max_velocity(50)

    restore_robot_pose(robot, "posbackup.json")
    robot.move_to_home_pose()

    # conexión principal
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    sock.connect((HOST, PORT))
    print("Conectado a servidor principal")

    # segunda conexión
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock2.settimeout(0.2)
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
        backup_robot_pose(robot, "posbackup.json")
        robot.close_connection()


if __name__ == "__main__":
    main()