import sys
import os
import pandas as pd
import networkx as nx
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from algorithms import brute_force_solve, nearest_neighbor_solve, genetic_solve

# Configuración inicial
sys.path.insert(0, str(Path(__file__).parent))

# Crear aplicación Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Variables de aplicación
app.graph = None
app.points_of_interest = []
app.distance_matrix = {}

def precompute_distances(graph, points):
    """Precalcula distancias entre todos los puntos"""
    matrix = {}
    for i in points:
        matrix[i] = {}
        for j in points:
            if i != j:
                matrix[i][j] = nx.shortest_path_length(graph, i, j, weight='weight')
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

        df = pd.read_csv(file)
        required_columns = {'origen', 'destino', 'distancia'}
        if not required_columns.issubset(df.columns):
            return jsonify({"error": "Invalid file format"}), 400

        app.graph = nx.Graph()
        for _, row in df.iterrows():
            app.graph.add_edge(row['origen'], row['destino'], weight=row['distancia'])

        return jsonify({
            "status": "success",
            "nodes": list(app.graph.nodes()),
            "edges": list(app.graph.edges())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load_points', methods=['POST'])
def load_points():
    try:
        if not app.graph:
            return jsonify({"error": "Load road network first"}), 400

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        content = file.read().decode('utf-8')
        points = [p.strip() for p in content.splitlines() if p.strip()]

        invalid_points = [p for p in points if p not in app.graph]
        if invalid_points:
            return jsonify({"error": f"Invalid points: {', '.join(invalid_points)}"}), 400

        # Asegurar que es un ciclo (comienza y termina en el mismo punto)
        if points[0] != points[-1]:
            points.append(points[0])
        
        app.points_of_interest = points
        app.distance_matrix = precompute_distances(app.graph, points)
        
        return jsonify({
            "status": "success",
            "points": points
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    if not os.path.exists('static/css/styles.css'):
        with open('static/css/styles.css', 'w') as f:
            f.write("body { font-family: Arial; }")
    
    if not os.path.exists('static/js/app.js'):
        with open('static/js/app.js', 'w') as f:
            f.write("console.log('App loaded');")
    
    app.run(debug=True, host='0.0.0.0', port=5000)