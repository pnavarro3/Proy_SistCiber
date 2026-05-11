"""
PruebaComTCPIP.py
-----------------
Conecta a Simulink por TCP/IP, envia bytes uint8 y cierra la conexion.
"""

import socket
HOST = "10.209.2.100"   # IP de Simulink
PORT = 1000           # Puerto del bloque TCP/IP Receive de Simulink

def enviar_3_bytes_utf8(sock: socket.socket, texto: str) -> None:
    """Envia exactamente 3 bytes por el socket usando codificacion UTF-8.
    - Si la representacion UTF-8 tiene menos de 3 bytes, se rellena con \x00.
    - Si tiene mas de 3 bytes, se trunca a 3 bytes.
    """
    b = texto.encode("utf-8")
    if len(b) < 3:
        b = b + (b"\x00" * (3 - len(b)))
    elif len(b) > 3:
        b = b[:3]
    sock.sendall(b)
    print("  Enviado:", " ".join(f"0x{byte:02X}" for byte in b))


def enviar_bytes(sock: socket.socket, vals) -> None:
    """Enviar una lista de bytes (enteros 0-255). Se ajusta a exactamente 3 bytes."""
    # convertir a lista de enteros
    bytes_list = [int(x) for x in vals]
    # normalizar a 3 bytes
    if len(bytes_list) < 3:
        bytes_list = bytes_list + [0] * (3 - len(bytes_list))
    elif len(bytes_list) > 3:
        bytes_list = bytes_list[:3]
    for b in bytes_list:
        if not (0 <= b <= 255):
            raise ValueError(f"Byte fuera de rango: {b}")
    sock.sendall(bytes(bytes_list))
    print("  Enviado:", " ".join(f"0x{b:02X}" for b in bytes_list))

if __name__ == "__main__":
    print(f"Conectando a {HOST}:{PORT} ...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Conexion establecida. Opciones:\n - Escribe 3 bytes en hex/dec separados por espacios (ej: 0x80 0x00 0x00 o 128 0 0)\n - Escribe texto libre (se codifica en UTF-8 y se ajusta a 3 bytes)\n - Escribe q para cerrar.\n")
        while True:
            entrada = input("Entrada: ").strip()
            if entrada.lower() == "q":
                print("Cerrando conexion.")
                break
            # intentar interpretar como lista de bytes (hex o decimal)
            tokens = entrada.split()
            parsed_as_bytes = False
            if len(tokens) >= 1:
                try:
                    vals = [int(t, 0) for t in tokens]
                    # si la conversion funciona y hay al menos un valor, enviamos como bytes
                    if len(vals) >= 1:
                        enviar_bytes(s, vals)
                        parsed_as_bytes = True
                except Exception:
                    parsed_as_bytes = False
            if not parsed_as_bytes:
                try:
                    enviar_3_bytes_utf8(s, entrada)
                except Exception as e:
                    print(f"  Error: {e}")
