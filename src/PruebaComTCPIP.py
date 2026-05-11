"""
PruebaComTCPIP.py
-----------------
Conecta a Simulink por TCP/IP, envia y recibe bytes uint8.
"""

import socket
import threading

HOST = "10.209.2.65"   # IP de Simulink
PORT = 5000            # Puerto del bloque TCP/IP de Simulink

BUFFER_SIZE = 1024     # Tamaño máximo del buffer de recepción


def enviar_3_bytes_utf8(sock: socket.socket, texto: str) -> None:
    """Envia exactamente 3 bytes por el socket usando codificacion UTF-8."""
    b = texto.encode("utf-8")
    if len(b) < 3:
        b = b + (b"\x00" * (3 - len(b)))
    elif len(b) > 3:
        b = b[:3]
    sock.sendall(b)
    print("  Enviado:", " ".join(f"0x{byte:02X}" for byte in b))


def enviar_bytes(sock: socket.socket, vals) -> None:
    """Enviar una lista de bytes (enteros 0-255). Se ajusta a exactamente 3 bytes."""
    bytes_list = [int(x) for x in vals]
    if len(bytes_list) < 3:
        bytes_list = bytes_list + [0] * (3 - len(bytes_list))
    elif len(bytes_list) > 3:
        bytes_list = bytes_list[:3]
    for b in bytes_list:
        if b < 0 or b > 255:
            raise ValueError(f"Valor fuera de rango uint8: {b}")
    data = bytes(bytes_list)
    sock.sendall(data)
    print("  Enviado:", " ".join(f"0x{byte:02X}" for byte in data))


def recibir_mensajes(sock: socket.socket, parar_evento: threading.Event = None) -> None:
    """Recibe mensajes continuamente por TCP/IP y los muestra por consola.
    Se detiene cuando se cierra la conexión o se activa parar_evento.
    """
    print(f"[RX] Escuchando mensajes en {HOST}:{PORT} ...")
    while True:
        if parar_evento and parar_evento.is_set():
            break
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("[RX] Conexión cerrada por el remoto.")
                break
            # Mostrar como hex
            hex_str = " ".join(f"0x{b:02X}" for b in data)
            # Mostrar como enteros
            int_str = ", ".join(str(b) for b in data)
            # Intentar mostrar como texto
            try:
                texto = data.decode("utf-8", errors="replace")
            except Exception:
                texto = ""
            print(f"  [RX] {len(data)} bytes | HEX: {hex_str} | INT: {int_str} | TXT: '{texto}'")
        except socket.timeout:
            continue
        except OSError as e:
            print(f"[RX] Error de socket: {e}")
            break


def main():
    print(f"Conectando a {HOST}:{PORT} ...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        sock.settimeout(1.0)  # timeout de 1s para poder comprobar parada
        print("Conexión establecida.\n")

        parar = threading.Event()

        # Hilo de recepción en segundo plano
        hilo_rx = threading.Thread(target=recibir_mensajes, args=(sock, parar), daemon=True)
        hilo_rx.start()

        print("Comandos:")
        print("  t <texto>       -> Enviar 3 bytes UTF-8")
        print("  b <n1> <n2> ... -> Enviar bytes (enteros 0-255)")
        print("  q               -> Salir\n")

        try:
            while True:
                entrada = input(">> ").strip()
                if not entrada:
                    continue
                if entrada.lower() == "q":
                    break
                partes = entrada.split(maxsplit=1)
                cmd = partes[0].lower()

                if cmd == "t" and len(partes) > 1:
                    enviar_3_bytes_utf8(sock, partes[1])
                elif cmd == "b" and len(partes) > 1:
                    valores = partes[1].split()
                    enviar_bytes(sock, valores)
                else:
                    print("  Comando no reconocido. Usa 't <texto>', 'b <n1> <n2> ...' o 'q'.")
        except KeyboardInterrupt:
            print("\nInterrumpido por el usuario.")

        parar.set()
        print("Cerrando conexión...")

    print("Conexión cerrada.")


if __name__ == "__main__":
    main()