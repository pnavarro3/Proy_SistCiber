import socket
import time
import random
from pyniryo import NiryoRobot
from VisionRobot import procesar_tablero_3x3_azules
from Ned2_ULL import backup_robot_pose, restore_robot_pose

# ─── Configuración TCP/IP ─────────────────────────────────────
HOST = "10.209.2.100"
PORT = 1000

# ─── Constantes del juego ─────────────────────────────────────
POSICIONES_TABLERO = [1, 2, 3, 4, 5, 6, 7, 8, 9]
COMBINACIONES_GANADORAS = [
    {1, 2, 3}, {4, 5, 6}, {7, 8, 9},   # filas
    {1, 4, 7}, {2, 5, 8}, {3, 6, 9},   # columnas
    {1, 5, 9}, {3, 5, 7},              # diagonales
]
MAX_TURNOS = 30


# ═══════════════════════════════════════════════════════════════
#  Comunicación TCP/IP
# ═══════════════════════════════════════════════════════════════

def enviar_mensaje(sock, mensaje):
    """Envía un mensaje con terminador \\n."""
    sock.sendall((mensaje + "\n").encode("utf-8"))
    print(f"  -> Enviado: {mensaje}")


def recibir_mensaje(sock):
    """Recibe un mensaje hasta encontrar \\n o \\r\\n."""
    buffer = b""
    while True:
        dato = sock.recv(1)
        if not dato:
            raise ConnectionError("Conexión cerrada por el servidor.")
        if dato in (b"\n", b"\r"):
            if buffer:
                break
            continue
        buffer += dato
    mensaje = buffer.decode("utf-8").strip()
    print(f"  <- Recibido: {mensaje}")
    return mensaje


# ═══════════════════════════════════════════════════════════════
#  Movimiento del robot
# ═══════════════════════════════════════════════════════════════

def nombre_pose(posicion):
    """Convierte el identificador de comunicación al nombre real de la pose del robot.

    Comunicación usa números ('1'..'9') o 'alm1'..'alm3'.
    El robot tiene poses llamadas 'pos1'..'pos9' y 'alm1'..'alm3'.
    """
    if posicion.startswith("alm"):
        return posicion          # alm1, alm2, alm3 → igual
    return f"pos{posicion}"     # "1" → "pos1", etc.


def nombre_aprox(posicion):
    """Devuelve el nombre de la pose de aproximación para una posición."""
    if posicion.startswith("alm"):
        return "aproxalm"
    return f"aprox{posicion}"   # "1" → "aprox1", etc.


def mover_ficha(robot, origen, destino):
    """
    Secuencia completa de pick-and-place:
      aprox_origen -> pos_origen (grasp) -> aprox_origen ->
      aprox_destino -> pos_destino (release) -> aprox_destino -> vista_gen

    Nombres de poses del robot: pos1..pos9 para el tablero, alm1..alm3 para almacén.
    Aproximaciones: aprox1..aprox9 y aproxalm.
    Reglas de tiempo: 3 s tras cada robot.move(), 1 s tras cada operación de pinza.
    """
    aprox_orig = nombre_aprox(origen)
    pose_orig  = nombre_pose(origen)
    aprox_dest = nombre_aprox(destino)
    pose_dest  = nombre_pose(destino)

    robot.clear_collision_detected()

    # 1. Ir a aproximación del origen
    robot.move(robot.get_pose_saved(aprox_orig))
    time.sleep(3)

    # 2. Bajar al origen
    robot.move(robot.get_pose_saved(pose_orig))
    time.sleep(3)

    # 3. Cerrar pinza
    robot.grasp_with_tool()
    time.sleep(1)

    # 4. Subir a aproximación del origen
    robot.move(robot.get_pose_saved(aprox_orig))
    time.sleep(3)

    # 5. Ir a aproximación del destino
    robot.move(robot.get_pose_saved(aprox_dest))
    time.sleep(3)

    # 6. Bajar al destino
    robot.move(robot.get_pose_saved(pose_dest))
    time.sleep(3)

    # 7. Abrir pinza
    robot.release_with_tool()
    time.sleep(1)

    # 8. Subir a aproximación del destino
    robot.move(robot.get_pose_saved(aprox_dest))
    time.sleep(3)

    # 9. Ir a posición de observación
    robot.move(robot.get_pose_saved("vista_gen"))
    time.sleep(3)


# ═══════════════════════════════════════════════════════════════
#  Lógica del juego
# ═══════════════════════════════════════════════════════════════

def verificar_victoria(posiciones):
    """Comprueba si un conjunto de posiciones forma línea ganadora."""
    s = set(posiciones)
    return any(combo.issubset(s) for combo in COMBINACIONES_GANADORAS)


def casillas_libres(propias, rival):
    """Devuelve casillas del tablero no ocupadas."""
    ocupadas = set(propias) | set(rival)
    return [c for c in POSICIONES_TABLERO if c not in ocupadas]


def construir_act(posiciones_rival):
    """Construye mensaje ACT p1 p2 p3 a partir de las posiciones detectadas."""
    p = [0, 0, 0]
    for i, pos in enumerate(posiciones_rival[:3]):
        p[i] = pos
    return f"ACT {p[0]} {p[1]} {p[2]}"


# ═══════════════════════════════════════════════════════════════
#  IA – modo automático (dificultad media)
# ═══════════════════════════════════════════════════════════════

def _minimax_colocacion(propias, rival, es_max, prof=0, max_prof=6):
    """Minimax para la fase de colocación (fichas desde almacén al tablero)."""
    if verificar_victoria(propias):
        return 10 - prof
    if verificar_victoria(rival):
        return prof - 10
    if prof >= max_prof:
        return 0

    libres = casillas_libres(propias, rival)
    if not libres:
        return 0

    if es_max:
        mejor = -float("inf")
        for c in libres:
            v = _minimax_colocacion(propias + [c], rival, False, prof + 1, max_prof)
            mejor = max(mejor, v)
        return mejor
    else:
        mejor = float("inf")
        for c in libres:
            v = _minimax_colocacion(propias, rival + [c], True, prof + 1, max_prof)
            mejor = min(mejor, v)
        return mejor


def _minimax_movimiento(propias, rival, es_max, prof=0, max_prof=4):
    """Minimax para la fase de movimiento (3 fichas por jugador en tablero)."""
    if verificar_victoria(propias):
        return 10 - prof
    if verificar_victoria(rival):
        return prof - 10
    if prof >= max_prof:
        return 0

    if es_max:
        mejor = -float("inf")
        for i, ficha in enumerate(propias):
            sin = propias[:i] + propias[i + 1:]
            for c in casillas_libres(sin, rival):
                v = _minimax_movimiento(sin + [c], rival, False, prof + 1, max_prof)
                mejor = max(mejor, v)
        return mejor if mejor != -float("inf") else 0
    else:
        mejor = float("inf")
        for i, ficha in enumerate(rival):
            sin = rival[:i] + rival[i + 1:]
            for c in casillas_libres(propias, sin):
                v = _minimax_movimiento(propias, sin + [c], True, prof + 1, max_prof)
                mejor = min(mejor, v)
        return mejor if mejor != float("inf") else 0


def decidir_jugada(fichas_propias, fichas_rival):
    """
    Decide la mejor jugada en modo automático.
    Devuelve (origen, destino) como cadenas de texto.
    """
    if len(fichas_propias) < 3:
        # ── Fase de colocación: mover ficha del almacén al tablero ──
        origen = f"alm{len(fichas_propias) + 1}"
        libres = casillas_libres(fichas_propias, fichas_rival)
        mejor_dest, mejor_val = None, -float("inf")

        for c in libres:
            v = _minimax_colocacion(fichas_propias + [c], fichas_rival, False)
            if v > mejor_val:
                mejor_val = v
                mejor_dest = c

        # 20% de aleatoriedad para dificultad media
        if random.random() < 0.2 and libres:
            mejor_dest = random.choice(libres)

        return origen, str(mejor_dest)

    else:
        # ── Fase de movimiento: mover ficha dentro del tablero ──
        mejor_orig, mejor_dest, mejor_val = None, None, -float("inf")

        for i, ficha in enumerate(fichas_propias):
            sin = fichas_propias[:i] + fichas_propias[i + 1:]
            for c in casillas_libres(sin, fichas_rival):
                v = _minimax_movimiento(sin + [c], fichas_rival, False)
                if v > mejor_val:
                    mejor_val = v
                    mejor_orig = ficha
                    mejor_dest = c

        # 15% de aleatoriedad para dificultad media
        if random.random() < 0.15 and fichas_propias:
            mejor_orig = random.choice(fichas_propias)
            sin = [f for f in fichas_propias if f != mejor_orig]
            libres = casillas_libres(sin, fichas_rival)
            if libres:
                mejor_dest = random.choice(libres)

        return str(mejor_orig), str(mejor_dest)


# ═══════════════════════════════════════════════════════════════
#  Turno del rival y detección por cámara
# ═══════════════════════════════════════════════════════════════

def esperar_turno_rival():
    """Espera a que el rival termine su turno (escribir 'f' + Enter)."""
    print("Esperando fin de turno del rival (escribe 'f' + Enter)...")
    while True:
        tecla = input("  > ").strip().lower()
        if tecla == "f":
            print("Turno del rival finalizado.")
            return


def detectar_fichas_rival(robot):
    """Captura imagen con la cámara y detecta posiciones de fichas rivales."""
    return procesar_tablero_3x3_azules(robot)


# ═══════════════════════════════════════════════════════════════
#  Bucle principal de partida
# ═══════════════════════════════════════════════════════════════

def partida(robot, sock):
    """Gestiona una partida completa de 3 en raya."""

    # ── Esperar mensaje INI ──
    print("\nEsperando inicio de partida (INI)...")
    modo = None
    while modo is None:
        msg = recibir_mensaje(sock)
        partes = msg.split()
        if len(partes) >= 2 and partes[0] == "INI":
            if partes[1].upper() in ("MAN", "AUT"):
                modo = partes[1].upper()
            else:
                print(f"Modo '{partes[1]}' no soportado. Esperando INI válido...")

    print(f"Partida iniciada en modo: {modo}")
    robot.say("Empieza la partida, que gane el mejor!", 3)

    # ── Estado del juego ──
    fichas_propias = []                          # posiciones en tablero (int)
    almacen = ["alm1", "alm2", "alm3"]          # fichas pendientes de colocar
    fichas_rival = []                            # posiciones en tablero (int)
    turno = 0

    while turno < MAX_TURNOS:
        turno += 1
        print(f"\n{'='*40}")
        print(f"  TURNO {turno}  (robot)")
        print(f"{'='*40}")
        print(f"  Fichas propias: {fichas_propias}")
        print(f"  Fichas rival:   {fichas_rival}")
        print(f"  Almacén:        {almacen}")

        # ── Decisión de jugada ──
        if modo == "MAN":
            # Esperar orden MOV del PC central
            print("Esperando orden MOV del PC central...")
            while True:
                msg = recibir_mensaje(sock)
                partes = msg.split()
                if len(partes) >= 3 and partes[0] == "MOV":
                    origen, destino = partes[1], partes[2]
                    break
                print(f"Mensaje inesperado: {msg}")

        else:  # AUT
            robot.say("Estoy pensando, espera un momento.", 3)
            origen, destino = decidir_jugada(fichas_propias, fichas_rival)
            print(f"Decisión IA: {origen} -> {destino}")
            enviar_mensaje(sock, "DEC")

        # ── Ejecutar movimiento del robot ──
        print(f"Moviendo ficha: {origen} -> {destino}")
        robot.say("Voy a mover mi ficha.", 3)
        mover_ficha(robot, origen, destino)

        # ── Actualizar estado propio ──
        destino_int = int(destino)
        if origen.startswith("alm"):
            if origen in almacen:
                almacen.remove(origen)
            fichas_propias.append(destino_int)
        else:
            origen_int = int(origen)
            if origen_int in fichas_propias:
                fichas_propias.remove(origen_int)
            fichas_propias.append(destino_int)

        # ── Fin de turno robot ──
        enviar_mensaje(sock, "FTU")

        # ── Comprobar victoria del robot (lógica interna) ──
        # fichas_propias se actualiza desde los MOV recibidos/decididos,
        # por lo que la verificación es puramente lógica (sin cámara).
        if verificar_victoria(fichas_propias):
            print("\n*** VICTORIA ***")
            robot.say("He ganado! Fin de la partida.", 3)
            enviar_mensaje(sock, "FIN VIC")
            return

        # ── Turno del rival ──
        print(f"\n--- Turno del rival ---")
        robot.say("Es tu turno, haz tu jugada.", 3)
        esperar_turno_rival()

        # ── Detectar fichas del rival con cámara (visión) ──
        # Las posiciones del rival se obtienen exclusivamente mediante
        # la cámara del robot, sin depender de lógica interna.
        fichas_rival = detectar_fichas_rival(robot)
        print(f"Fichas rival detectadas por cámara: {fichas_rival}")

        # ── Enviar actualización ACT ──
        enviar_mensaje(sock, construir_act(fichas_rival))
        # Informar también fin de turno del rival al PC central
        enviar_mensaje(sock, "FTU")

        # ── Comprobar derrota (posiciones del rival por visión) ──
        if verificar_victoria(fichas_rival):
            print("\n--- DERROTA ---")
            robot.say("Has ganado, felicitaciones! Fin de la partida.", 3)
            enviar_mensaje(sock, "FIN DER")
            return

    # Si se agotan los turnos, empate
    print("\nLímite de turnos alcanzado – EMPATE")
    robot.say("Empate! Ha sido una partida muy igualada.", 3)
    enviar_mensaje(sock, "FIN EMP")


# ═══════════════════════════════════════════════════════════════
#  Punto de entrada
# ═══════════════════════════════════════════════════════════════

def main():
    # Conectar al robot
    robot = NiryoRobot("10.10.10.10")
    robot.calibrate_auto()
    robot.update_tool()
    robot.set_arm_max_velocity(50)

    # Restaurar poses guardadas
    backup_file = "posbackup.json"
    try:
        restore_robot_pose(robot, backup_file)
        print("Poses restauradas desde backup.")
    except FileNotFoundError:
        print("No se encontró archivo de backup.")

    # Mover a posición de observación inicial
    robot.move(robot.get_pose_saved("vista_gen"))

    # Conectar al PC central por TCP/IP
    print(f"\nConectando a {HOST}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        print("Conexión TCP/IP establecida.\n")

        partida(robot, sock)

    except ConnectionRefusedError:
        print("ERROR: No se pudo conectar al PC central.")
    except ConnectionError as e:
        print(f"ERROR de conexión: {e}")
    finally:
        sock.close()
        backup_robot_pose(robot, backup_file)
        robot.close_connection()
        print("Conexiones cerradas.")


if __name__ == "__main__":
    main()
