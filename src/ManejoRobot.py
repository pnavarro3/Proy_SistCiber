from pyniryo import NiryoRobot
from Ned2_ULL import backup_robot_pose, restore_robot_pose, create_robot_pose, calibration
from VisionRobot import procesar_tablero_3x3_azules

robot = NiryoRobot('10.10.10.10')

# Calibrar el robot y actualizar el efector final
robot.calibrate_auto()
robot.update_tool()

# Seleccionar velocidad del robot
robot.set_arm_max_velocity(50)

backup_file = "posbackup.json"

# Restaurar poses guardadas si existe el backup
try:
    restore_robot_pose(robot, backup_file)
    print("Poses restauradas desde backup.")
except FileNotFoundError:
    print("No se encontró archivo de backup. Se empezará sin poses guardadas.")

# Variable para rastrear la última posición del robot
posicion_actual = "home"
robot.say("Hola Ruben", 3)

print("\nPrograma para manejar el robot.")
print("Opciones disponibles:")
print("1. Guardar una nueva posición.")
print("2. Moverse a una posición guardada.")
print("3. Analizar cuadrícula con cámara (detectar azules).")
print("4. Calibrar HSV de la cámara.")
print("5. Salir del programa.\n")

while True:
    # Mostrar el menú y obtener la opción del usuario
    option = input("Selecciona una opción (1, 2, 3, 4, 5): ").strip()

    if option == "1":
        # Guardar una nueva posición
        pose_name = input("Introduce el nombre de la posición a guardar: ").strip()
        if pose_name:
            create_robot_pose(robot, pose_name)
            print(f"Pose '{pose_name}' guardada correctamente.")
        else:
            print("El nombre de la posición no puede estar vacío.")

    elif option == "2":
        # Moverse a una posición guardada
        saved_poses = robot.get_saved_pose_list()
        if not saved_poses:
            print("No hay posiciones guardadas.")
        else:
            print(f"Posiciones disponibles: {saved_poses}")
            pose_to_move = input("Introduce el nombre de la posición: ").strip()

            if pose_to_move in saved_poses:
                pose = robot.get_pose_saved(pose_to_move)

                # Limpiar estado de colisión antes de moverse
                robot.clear_collision_detected()

                robot.move(pose)
                posicion_actual = pose_to_move
                print(f"Movido a la posición '{pose_to_move}'.")
            else:
                print(f"La posición '{pose_to_move}' no existe.")

    elif option == "3":
        # Analizar cuadrícula con visión
        if posicion_actual != "vista_gen":
            print("El robot debe estar en la posición 'vista_gen' para capturar la imagen.")
            print(f"Posición actual: '{posicion_actual}'. Muévete primero con la opción 2.")
        else:
            print("\nAnalizando zona de trabajo con cámara...")
            posiciones = procesar_tablero_3x3_azules(robot)

            if posiciones:
                print(f"Cuadrados azules en posiciones: {posiciones}")
            else:
                print("No se encontraron cuadrados azules.")


    elif option == "4":
        print("\nIniciando calibración HSV...")
        calibration_data = calibration(robot)
        print(f"Calibración final: {calibration_data}")

    elif option == "5":
        # Salir del programa
        print("Saliendo del programa...")
        break

    else:
        print("Opción no válida. Por favor, selecciona 1, 2, 3, 4 o 5.")

# Crear un backup de las poses guardadas
backup_robot_pose(robot, backup_file)
print(f"Backup creado en {backup_file} con las poses guardadas.")

# Finalizar la conexión con el robot
robot.close_connection()