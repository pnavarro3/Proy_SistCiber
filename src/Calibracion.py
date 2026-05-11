import cv2
import numpy as np
from pyniryo import NiryoRobot, image_functions

robot = NiryoRobot('10.10.10.10')
robot.calibrate_auto()

# Capturar imagen del robot
img_compressed = robot.get_img_compressed()
img = image_functions.uncompress_image(img_compressed)

robot.close_connection()

# Convertir a HSV
img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Crear ventana con trackbars
cv2.namedWindow("Calibracion HSV")
cv2.createTrackbar("H min", "Calibracion HSV", 0, 179, lambda x: None)
cv2.createTrackbar("S min", "Calibracion HSV", 0, 255, lambda x: None)
cv2.createTrackbar("V min", "Calibracion HSV", 0, 255, lambda x: None)
cv2.createTrackbar("H max", "Calibracion HSV", 179, 179, lambda x: None)
cv2.createTrackbar("S max", "Calibracion HSV", 255, 255, lambda x: None)
cv2.createTrackbar("V max", "Calibracion HSV", 255, 255, lambda x: None)

while True:
    # Leer valores de los trackbars
    h_min = cv2.getTrackbarPos("H min", "Calibracion HSV")
    s_min = cv2.getTrackbarPos("S min", "Calibracion HSV")
    v_min = cv2.getTrackbarPos("V min", "Calibracion HSV")
    h_max = cv2.getTrackbarPos("H max", "Calibracion HSV")
    s_max = cv2.getTrackbarPos("S max", "Calibracion HSV")
    v_max = cv2.getTrackbarPos("V max", "Calibracion HSV")

    # Aplicar máscara HSV
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(img_hsv, lower, upper)
    result = cv2.bitwise_and(img, img, mask=mask)

    # Mostrar imágenes
    cv2.imshow("Imagen Original", img)
    cv2.imshow("Mascara", mask)
    cv2.imshow("Resultado", result)

    # Mostrar valores actuales en consola
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print(f"\nValores HSV seleccionados:")
        print(f"  hsv_min = [{h_min}, {s_min}, {v_min}]")
        print(f"  hsv_max = [{h_max}, {s_max}, {v_max}]")
        break

cv2.destroyAllWindows()