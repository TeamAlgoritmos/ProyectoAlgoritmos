import sys
import os
import pandas as pd
import networkx as nx
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from algorithms import brute_force_solve, nearest_neighbor_solve, genetic_solve
from geopy.distance import geodesic # Necesaria para distancias geográficas

# Configuración inicial
sys.path.insert(0, str(Path(__file__).parent))

# Crear aplicación Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Variables de aplicación
app.graph = None
app.points_of_interest = []
app.distance_matrix = {}
app.point_coords = {}

def precompute_distances(graph, points):
    """Precalcula distancias entre todos los puntos de interés usando el grafo."""
    matrix = {}
    for i in points:
        matrix[i] = {}
        for j in points:
            if i != j:
                # Calculamos la distancia geográfica directamente si tenemos coordenadas en los nodos del grafo
                try:
                    point_i_coords = (graph.nodes[i]['Y'], graph.nodes[i]['X'])
                    point_j_coords = (graph.nodes[j]['Y'], graph.nodes[j]['X'])
                    matrix[i][j] = geodesic(point_i_coords, point_j_coords).meters # Distancia en metros
                except KeyError:
                    # Si no hay coordenadas, fallar o manejar apropiadamente
                    print(f"Advertencia: No se encontraron coordenadas para los nodos {i} o {j}")
                    matrix[i][j] = float('inf') # O algún otro valor que indique inaccesibilidad
    return matrix

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/load_network', methods=['POST'])
def load_network():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Leemos el archivo de la red vial
        network_df = pd.read_csv(file)
        required_columns = {'origen', 'destino', 'distancia'}
        if not required_columns.issubset(network_df.columns):
            return jsonify({"error": "El archivo debe contener las columnas origen, destino y distancia"}), 400

        # Creamos el grafo
        app.graph = nx.Graph()
        
        # Añadimos las aristas con sus distancias
        for _, row in network_df.iterrows():
            app.graph.add_edge(str(row['origen']), str(row['destino']), weight=row['distancia'])

        # Devolvemos la información de la red
        return jsonify({
            "status": "success",
            "nodes": list(app.graph.nodes()),
            "edges": list(app.graph.edges(data=True))
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load_points', methods=['POST'])
def load_points():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        points_df = pd.read_csv(file)
        required_columns = {'X', 'Y', 'id'}
        if not required_columns.issubset(points_df.columns):
            return jsonify({"error": "El archivo de puntos de interés debe contener las columnas X, Y, e id"}), 400

        # Almacenar los puntos y sus coordenadas
        app.points_of_interest = [str(id) for id in points_df['id'].tolist()]
        app.point_coords = points_df.set_index('id')[['X', 'Y']].T.to_dict('dict')

        # Precalcular la matriz de distancias
        app.distance_matrix = precompute_distances(app.graph, app.points_of_interest)

        # Devolver la lista de puntos con coordenadas para el mapa
        points_list = points_df[['X', 'Y', 'id']].to_dict('records')

        return jsonify({
            "status": "success",
            "points": points_list
        })

    except Exception as e:
        return jsonify({"error": f"Error al cargar puntos de interés: {str(e)}"}), 500

@app.route('/api/solve_tsp', methods=['POST'])
def solve_tsp():
    try:
        if not app.graph:
            return jsonify({"error": "Load road network first"}), 400

        if len(app.points_of_interest) < 3:
            return jsonify({"error": "Need at least 2 unique points"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        algorithm = data.get('algorithm')
        if not algorithm:
            return jsonify({"error": "No algorithm specified"}), 400

        # Ejecutar el algoritmo seleccionado
        if algorithm == 'brute_force':
            path, distance, exec_time = brute_force_solve(app.graph, app.points_of_interest, app.distance_matrix)
        elif algorithm == 'nearest_neighbor':
            path, distance, exec_time = nearest_neighbor_solve(app.graph, app.points_of_interest, app.distance_matrix)
        elif algorithm == 'genetic':
            path, distance, exec_time = genetic_solve(app.graph, app.points_of_interest, app.distance_matrix)
        else:
            return jsonify({"error": "Invalid algorithm"}), 400

        # Formatear la ruta para visualización
        formatted_path = " → ".join(path)
        
        return jsonify({
            "status": "success",
            "algorithm": algorithm.replace('_', ' ').title(),
            "path": formatted_path,
            "distance": distance,
            "execution_time_ms": round(exec_time * 1000, 2),  # Tiempo en milisegundos
            "nodes_visited": len(path),
            "efficiency": round(distance / exec_time, 2) if exec_time > 0 else 0
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/api/map_points', methods=['GET'])
def get_map_points():
    """Devuelve los puntos de interés cargados con sus coordenadas para mostrar en el mapa."""
    try:
        if not app.points_of_interest:
            return jsonify([]), 200 # Devuelve lista vacía si no hay puntos cargados

        # Construir la lista de puntos con coordenadas a partir de los puntos de interés y sus coordenadas almacenadas
        map_points_list = []
        # Usar un set para evitar duplicados si el primer y ultimo punto son el mismo en points_of_interest
        unique_points_to_map = list(dict.fromkeys(app.points_of_interest))
        
        for point_id in unique_points_to_map:
            if str(point_id) in app.point_coords:
                 coords = app.point_coords[str(point_id)]
                 map_points_list.append({'X': coords['X'], 'Y': coords['Y'], 'id': point_id})
            else:
                 print(f"Advertencia: Coordenadas no encontradas para el punto {point_id} para mostrar en el mapa.")

        return jsonify(map_points_list)

    except Exception as e:
        return jsonify({"error": f"Error al obtener puntos del mapa: {str(e)}"}), 500

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    if not os.path.exists('static/css/styles.css'):
        with open('static/css/styles.css', 'w') as f:
            f.write("body { font-family: Arial; }")
    
    if not os.path.exists('static/js/app.js'):
        with open('static/js/app.js', 'w') as f:
            f.write("console.log('App loaded');")
    
    app.run(debug=True, host='0.0.0.0', port=5001)