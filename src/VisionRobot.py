from pyniryo import NiryoRobot, ObjectColor, ObjectShape
from pyniryo.vision import image_functions
import cv2
import numpy as np


def procesar_tablero_3x3_azules(
    robot,
    ws_ratio=1.0,
    hsv_min=(97, 123, 116),
    hsv_max=(156, 255, 246),
    area_min_ratio=0.05,
):
    """
    Procesa la imagen capturada por el robot para obtener el estado de un tablero 3x3.
    1) Captura y descompresión de imagen.
    2) Corrección de perspectiva extrayendo el workspace como cuadrado.
    3) Segmentación de color azul (HSV).
    4) División en cuadrícula 3x3 y detección de casillas ocupadas.

            1 | 2 | 3
            ---------
            4 | 5 | 6
            ---------
            7 | 8 | 9
    """
    posiciones_encontradas = []

    img_compressed = robot.get_img_compressed()
    img = image_functions.uncompress_image(img_compressed)
    print("Imagen capturada correctamente.") 
    try:
        img_workspace = image_functions.extract_img_workspace(img, ws_ratio)
    except Exception as e:
        print(f"ERROR: No se pudo extraer la zona de trabajo: {e}")
        return posiciones_encontradas

    if img_workspace is None:
        print("ERROR: No se detectaron los marcadores de la zona de trabajo.")
        return posiciones_encontradas

    print("Zona de trabajo extraída y corregida correctamente.")
    #image_functions.show_img_and_wait_close("prueba", img_workspace)
    mascara_azul = image_functions.threshold_hsv(
        img_workspace, list(hsv_min), list(hsv_max)
    )

    kernel = np.ones((5, 5), np.uint8)
    mascara_azul = cv2.morphologyEx(mascara_azul, cv2.MORPH_OPEN, kernel)
    mascara_azul = cv2.morphologyEx(mascara_azul, cv2.MORPH_CLOSE, kernel)

    alto, ancho = img_workspace.shape[:2]
    ancho_celda = ancho / 3
    alto_celda = alto / 3

    contornos, _ = cv2.findContours(
        mascara_azul, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    area_minima = (ancho_celda * alto_celda) * area_min_ratio
    contornos_filtrados = [c for c in contornos if cv2.contourArea(c) > area_minima]

    ocupacion = np.zeros((3, 3), dtype=np.uint8)

    for contorno in contornos_filtrados:
        M = cv2.moments(contorno)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        col = min(int(cx / ancho_celda), 2)
        fila = min(int(cy / alto_celda), 2)
        ocupacion[fila, col] = 1

    for fila in range(3):
        for col in range(3):
            if ocupacion[fila, col] == 1:
                fila_inv = 2 - fila
                col_inv = 2 - col
                posiciones_encontradas.append(fila_inv * 3 + col_inv + 1)

    return posiciones_encontradas


def capturar_y_analizar_cuadricula(robot, workspace_name="workspace_1"):
    return procesar_tablero_3x3_azules(robot, ws_ratio=1.0)