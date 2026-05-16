# Sistema Ciberfísico 3 en Raya con Ned-2

Proyecto académico de Sistemas Ciberfísicos (ULL, curso 2025/26) para implementar y validar una partida de 3 en raya con robot Ned-2, visión artificial y supervisión remota desde un PC central.

## Resumen

El sistema se compone de dos nodos:

- PC central (Matlab/Simulink): supervisa estados, envía comandos de juego y muestra la evolución de la partida.
- PC del robot (Python): controla Ned-2, gestiona comunicación TCP/IP, procesa visión y ejecuta jugadas.

Incluye dos modos de operación:

- Manual: el operador decide el movimiento desde el PC central.
- Automático: el robot calcula su jugada mediante una heurística de victoria inmediata y elección de casilla libre.

## Estructura del repositorio

.
|- src/
|  |- ComRobot.py
|  |- Ned2_ULL.py
|  |- VisionRobot.py
|  |- Calibracion.py
|  |- ManejoRobot.py
|  |- PruebaComTCPIP.py
|  |- pruebaRuben.py
|- simulink/
|  |- SimulinkEmisor.m
|  |- SimulinkReceptor.m
|  |- InterpretarTablero.m
|  |- MensajeTurno.m
|- config/
|  |- posbackup.json
|- docs/
|  |- Documento_tecnico_final.tex
|  |- Documento_tecnico_final.pdf
|- context/
|- capturas/
|- .gitignore
|- README.md

## Componentes principales

### Python (PC robot)

- ComRobot.py: bucle principal de partida, sockets, lógica de turnos y movimiento pick-and-place.
- Ned2_ULL.py: utilidades de poses del robot, backup/restore y calibración HSV.
- VisionRobot.py: detección del tablero y extracción de casillas ocupadas desde la cámara del robot.

### Simulink/Matlab (PC central)

- SimulinkEmisor.m: formatea tramas de salida hacia el robot en buffer fijo (uint8 1x32).
- SimulinkReceptor.m: parsea mensajes de entrada, genera pulsos de evento y estado de tablero.
- InterpretarTablero.m: separa el vector 1x9 para uso en lógica/interfaz.
- MensajeTurno.m: mensaje de estado de turno para supervisión.

## Protocolo de comunicación

Mensajes de texto finalizados en salto de línea:

- PC central -> robot: INI MAN, INI AUT, INI COM, MOV origen destino.
- Robot -> PC central: DEC, ACT, FTJ, FTU, FIN VIC/DER/EMP.

## Requisitos técnicos

### Hardware

- Robot Ned-2 con pinza y cámara operativa.
- PC central para Simulink.
- PC de control del robot.
- Red del laboratorio (router + wifi) para ambos equipos.

### Software

- Python 3.8 o superior.
- Matlab/Simulink.
- pyniryo.
- opencv-python.
- numpy.

## Puesta en marcha rápida

1. Conectar router del laboratorio y ambos PCs a la red wifi de trabajo.
2. Revisar IPs y configurar la IP del PC robot tanto en Simulink como en ComRobot.py.
3. Encender y calibrar el Ned-2.
4. Calibrar HSV de cámara para detección de tablero.
5. Cargar poses/configuracion del robot.
6. Iniciar script de control en el PC robot.
7. Abrir modelo de Simulink en PC central y arrancar comunicación.
8. Seleccionar modo y pulsar Start.

## Documentación

- Informe editable en docs/Documento_tecnico_final.tex.
- Informe compilado en docs/Documento_tecnico_final.pdf.

## Política de versionado

El repositorio utiliza reglas en .gitignore para no subir carpetas de apoyo y limitar archivos rastreados en algunas rutas.

## Estado del proyecto

Sistema funcional en manual y automático, con validaciones de comunicación, seguridad de movimiento, visión y tiempos de ciclo recogidas en el documento técnico final.
