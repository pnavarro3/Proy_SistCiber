# Proyecto: Sistema Ciberfísico de 3 en Raya con Robot Ned-2

Proyecto desarrollado en la Universidad de La Laguna (ULL) para un sistema ciberfísico completo que integra visión, IA y robótica con el robot colaborativo Ned-2.

## Estructura del Proyecto

```
.
├── src/                           # Código fuente Python
│   ├── ComRobot.py               # Comunicación y control del robot
│   ├── VisionRobot.py            # Procesamiento de visión y detección del tablero
│   ├── Ned2_ULL.py               # Utilidades y calibración HSV del Ned-2
│   ├── ManejoRobot.py            # Gestión de movimientos y poses
│   ├── Calibracion.py            # Calibración del sistema
│   └── PruebaComTCPIP.py         # Pruebas de comunicación TCP/IP
│
├── simulink/                      # Sistemas de control en Simulink/Matlab
│   ├── SimulinkEmisor.m          # Interfaz emisora (PC central → Ned-2)
│   └── SimulinkReceptor.m        # Interfaz receptora (Ned-2 → PC central)
│
├── docs/                          # Documentación técnica
│   ├── Documento_tecnico_final.tex  # Informe técnico en LaTeX
│   ├── Documento_tecnico_final.pdf  # PDF compilado del informe
│   └── (archivos auxiliares LaTeX)
│
├── config/                        # Archivos de configuración
│   └── posbackup.json            # Backup de poses del robot
│
├── context/                       # Documentos de referencia del proyecto
│   ├── Documento_técnico.txt
│   ├── Documento_tecnico2.txt
│   ├── EnunciadoProyecto (1).txt
│   └── Requisitos 2 (1).txt
│
└── .gitignore                     # Configuración de Git

```

## Descripción de Componentes

### src/ - Código Fuente

- **ComRobot.py**: Núcleo de comunicación TCP/IP y control del robot. Implementa el protocolo basado en mensajes ASCII (INI, MOV, DEC, ACT, FTJ, FTU, FIN).
- **VisionRobot.py**: Sistema de visión. Procesa imágenes de la cámara RGB del robot, realiza segmentación HSV y corrección de perspectiva.
- **Ned2_ULL.py**: Utilidades específicas del Ned-2, incluyendo calibración HSV y funciones de API pyniryo.
- **ManejoRobot.py**: Gestión de movimientos, poses (almacén, aproximación, espera), límites de velocidad.
- **Calibracion.py**: Rutinas de calibración del sistema.
- **PruebaComTCPIP.py**: Suite de pruebas para validar la comunicación TCP/IP.

### simulink/ - Control en Simulink

- **SimulinkEmisor.m**: Máquina de estados y emisor desde PC central al robot.
- **SimulinkReceptor.m**: Receptor e integración de mensajes en el sistema.

### docs/ - Documentación

El informe técnico final consolida todo el trabajo:
- Arquitectura del sistema (PC central + PC del robot)
- Descripción técnica completa con tablas y figuras
- Validación de requisitos
- Guía de puesta en marcha

### config/ - Configuración

- **posbackup.json**: Almacenamiento persistente de poses y configuración del robot.

### context/ - Referencias

Documentos originales del proyecto:
- Enunciado del proyecto
- Documento técnico previos
- Especificación de requisitos

## Tecnologías

- **Lenguaje**: Python 3.x, Matlab/Simulink
- **Robot**: Ned-2 (6 DoF, cámara RGB, pinza integrada)
- **Control**: pyniryo API
- **Comunicación**: TCP/IP (puerto configurable)
- **Visión**: OpenCV, procesamiento HSV
- **IA**: Algoritmo Minimax para decisiones automáticas
- **Documentación**: LaTeX

## Comunicación TCP/IP

El protocolo usa mensajes de texto ASCII terminados en `\n`:
- **INI**: Inicialización y reset
- **MOV**: Movimiento del robot a coordenadas
- **DEC**: Decisión (modo IA)
- **ACT**: Acción de la pinza
- **FTJ**: Feedback del jugador
- **FTU**: Feedback del usuario
- **FIN**: Fin de partida

## Requisitos del Sistema

### Hardware
- PC Central (Simulink, estrategia, coordinación)
- PC Ned-2 (visión, movimiento, pinza)
- Robot Ned-2 con cámara RGB
- Red Ethernet entre PCs

### Software
- Python 3.8+
- Matlab/Simulink (para control)
- pyniryo
- OpenCV
- NumPy, SciPy

## Instalación y Puesta en Marcha

Ver `docs/Documento_tecnico_final.pdf` para instrucciones detalladas.

## Validación

El proyecto cumple con todos los requisitos especificados en `context/Requisitos 2 (1).txt`. Ver informe técnico final para matriz de trazabilidad.

## Licencia

Proyecto académico - Universidad de La Laguna

## Contacto

Para consultas sobre este proyecto, consulta los documentos técnicos incluidos.
