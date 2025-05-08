# Route Optimization System - TSP on Road Networks

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Descripción

Este proyecto implementa un sistema para optimizar el orden de visita de ubicaciones dentro de una red vial, resolviendo una variante del Problema del Viajante (TSP) donde la distancia entre puntos se calcula como el camino más corto en la red vial, no como distancia euclidiana.

## Características principales

- Carga y visualización de redes viales (nodos y aristas)
- Integración de puntos de interés en la red vial
- Implementación de 3 algoritmos para resolver el TSP:
  - Fuerza bruta (caso base)
  - Vecino más cercano
  - Algoritmo genético
- Visualización interactiva de resultados
- Comparación de rendimiento entre algoritmos

## Requisitos

- Python 3.8+
- Librerías principales:
  - Flask (para la aplicación web)
  - Leaflet/OpenLayers (para visualización de mapas)
  - NetworkX (para manejo de grafos)
  - Pandas (para procesamiento de datos)
 
##Estructura Proyecto

```text
ProyectoAlgoritmos/
├── src/                     # Código fuente principal
│   ├── __init__.py
│   ├── app.py               # Aplicación Flask principal
│   ├── algorithms/          # Implementación de algoritmos
│   │   ├── __init__.py
│   │   ├── brute_force.py
│   │   ├── nearest_neighbor.py
│   │   └── genetic.py
│   ├── utils/               # Utilidades
│   │   ├── graph_utils.py   # Manejo de grafos
│   │   └── file_utils.py    # Procesamiento de archivos
│   └── static/              # Archivos estáticos (CSS, JS)
│       ├── css/
│       └── js/
├── data/                    # Datos de ejemplo
│   ├── red_vial.csv         # Ejemplo red vial
│   └── puntos_interes.csv   # Ejemplo puntos de interés
├── tests/                   # Pruebas unitarias
│   ├── test_algorithms.py
│   └── test_utils.py
├── docs/                    # Documentación
│   └── technical_report.md
├── .gitignore               # Archivo para ignorar venv/ y otros
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación principal
```

## Instalación

1. Clonar el repositorio:
```bash
# Clonar repositorio
git clone https://github.com/TeamAlgoritmos/ProyectoAlgoritmos.git
cd ProyectoAlgoritmos

# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

