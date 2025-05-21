import os
import math
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Variables globales
app.graph: Optional[nx.Graph] = None
app.points_of_interest: List[str] = []
app.distance_matrix: Dict[str, Dict[str, float]] = {}
app.node_coords: Dict[str, Tuple[float, float]] = {}

# ------------------------------------------
# Funciones de utilidad mejoradas
# ------------------------------------------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en metros entre dos coordenadas geográficas."""
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def parse_xml(filepath: str) -> Dict:
    """Procesa archivos XML grandes con manejo robusto de conexiones."""
    print("Procesando archivo XML...")
    
    try:
        context = ET.iterparse(filepath, events=('start', 'end'))
        
        nodes = {}
        connections = []
        current_way = []
        
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'node':
                    try:
                        nodes[elem.get('id')] = {
                            'lat': float(elem.get('lat')),
                            'lon': float(elem.get('lon'))
                        }
                    except (TypeError, ValueError, AttributeError):
                        continue
                        
                elif elem.tag == 'way':
                    current_way = []
                    
            elif event == 'end':
                if elem.tag == 'nd' and current_way is not None:
                    ref = elem.get('ref')
                    if ref in nodes:
                        current_way.append(ref)
                        
                elif elem.tag == 'way':
                    if len(current_way) >= 2:
                        for i in range(len(current_way)-1):
                            connections.append((current_way[i], current_way[i+1]))
                    elem.clear()  # Liberar memoria
                    
        print(f"Nodos encontrados: {len(nodes)}")
        print(f"Conexiones válidas: {len(connections)}")
        
        return {
            'nodes': nodes,
            'connections': connections,
            'metadata': {
                'total_nodes': len(nodes),
                'total_edges': len(connections)
            }
        }
        
    except Exception as e:
        raise ValueError(f"Error al procesar XML: {str(e)}")

def create_graph(nodes: Dict, connections: List) -> nx.Graph:
    """Crea grafo NetworkX con validación robusta."""
    G = nx.Graph()
    
    # Añadir nodos
    for node_id, coords in nodes.items():
        G.add_node(node_id, pos=(coords['lat'], coords['lon']))
        app.node_coords[node_id] = (coords['lat'], coords['lon'])
    
    # Añadir conexiones
    for source, target in connections:
        try:
            pos1 = nodes[source]
            pos2 = nodes[target]
            distance = haversine_distance(
                pos1['lat'], pos1['lon'],
                pos2['lat'], pos2['lon']
            )
            G.add_edge(source, target, weight=distance)
        except KeyError:
            continue
    
    print(f"Grafo creado con {len(G.nodes())} nodos y {len(G.edges())} aristas")
    return G

def precompute_distances(graph: nx.Graph, points: List[str]) -> Dict[str, Dict[str, float]]:
    """Precalcula distancias entre puntos de interés con verificación de conectividad."""
    print("Precalculando matriz de distancias...")
    distance_matrix = {}
    
    for i in points:
        if i not in graph:
            raise ValueError(f"El nodo {i} no existe en el grafo")
            
        distance_matrix[i] = {}
        for j in points:
            if i != j:
                try:
                    distance_matrix[i][j] = nx.shortest_path_length(graph, i, j, weight='weight')
                except nx.NetworkXNoPath:
                    raise ValueError(f"Nodo {i} no alcanzable desde {j}")
    
    return distance_matrix

# ------------------------------------------
# Endpoints de la API (mejorados)
# ------------------------------------------

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
            return jsonify({"error": "No se proporcionó archivo"}), 400
        
        file = request.files['file']
        if not file.filename.lower().endswith('.xml'):
            return jsonify({"error": "Solo se aceptan archivos XML"}), 400

        temp_path = 'temp_network.xml'
        file.save(temp_path)
        
        try:
            xml_data = parse_xml(temp_path)
            app.graph = create_graph(xml_data['nodes'], xml_data['connections'])
            
            return jsonify({
                "status": "success",
                "message": "Red vial cargada correctamente",
                "stats": {
                    "nodes": len(app.graph.nodes()),
                    "edges": len(app.graph.edges())
                }
            })
        finally:
            try:
                os.remove(temp_path)
            except:
                pass

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load_points', methods=['POST'])
def load_points():
    try:
        if not app.graph:
            return jsonify({"error": "Primero cargue la red vial"}), 400

        if 'file' not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400
        
        file = request.files['file']
        if not (file.filename.lower().endswith('.tsv') or file.filename.lower().endswith('.csv')):
            return jsonify({"error": "Solo se aceptan archivos TSV o CSV"}), 400

        # Leer archivo
        sep = '\t' if file.filename.lower().endswith('.tsv') else ','
        df = pd.read_csv(file, sep=sep)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()
        required_cols = {'x', 'y', 'id'}
        
        if not required_cols.issubset(df.columns):
            return jsonify({
                "error": f"El archivo debe contener las columnas: {required_cols}",
                "columnas_recibidas": list(df.columns)
            }), 400

        # Procesar puntos con verificación de conectividad
        points = []
        problematic_points = []
        
        for _, row in df.iterrows():
            try:
                # Encontrar el nodo más cercano
                closest_node = min(
                    app.graph.nodes(),
                    key=lambda n: haversine_distance(
                        float(row['y']), float(row['x']),
                        app.node_coords[n][0], app.node_coords[n][1]
                    )
                )
                
                # Verificar que el nodo esté conectado
                if points:  # Solo verificar si ya hay puntos previos
                    if not nx.has_path(app.graph, points[0], closest_node):
                        problematic_points.append(f"Punto {row['id']} (nodo {closest_node}) no conectado")
                        continue
                
                points.append(closest_node)
            except Exception as e:
                problematic_points.append(f"Punto {row['id']}: {str(e)}")
                continue

        if len(points) < 2:
            return jsonify({
                "error": "Se necesitan al menos 2 puntos válidos",
                "details": problematic_points
            }), 400

        # Cerrar el ciclo solo si todos los puntos están conectados
        if points[0] != points[-1]:
            if nx.has_path(app.graph, points[-1], points[0]):
                points.append(points[0])
            else:
                problematic_points.append(f"No se puede cerrar el ciclo: nodo {points[-1]} no conectado a {points[0]}")

        app.points_of_interest = points
        
        try:
            app.distance_matrix = precompute_distances(app.graph, points)
        except ValueError as e:
            return jsonify({
                "error": "Problema de conectividad en los puntos",
                "details": str(e),
                "problematic_points": problematic_points
            }), 400
        
        response = {
            "status": "success",
            "points_loaded": len(points),
            "sample_points": points[:5]
        }
        
        if problematic_points:
            response["warnings"] = problematic_points
        
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/solve_tsp', methods=['POST'])
def solve_tsp():
    try:
        if not app.graph or not app.points_of_interest or not app.distance_matrix:
            raise ValueError("Datos incompletos. Cargue red y puntos primero")
        
        data = request.get_json()
        algorithm = data.get('algorithm', '').lower()
        
        # Verificar conectividad antes de resolver
        for i in range(len(app.points_of_interest)-1):
            if not nx.has_path(app.graph, app.points_of_interest[i], app.points_of_interest[i+1]):
                raise ValueError(f"No hay ruta entre {app.points_of_interest[i]} y {app.points_of_interest[i+1]}")
        
        if algorithm == 'nearest_neighbor':
            from algorithms import nearest_neighbor_solve
            path, distance, _ = nearest_neighbor_solve(app.graph, app.points_of_interest, app.distance_matrix)
        elif algorithm == 'genetic':
            from algorithms import genetic_solve
            path, distance, _ = genetic_solve(app.graph, app.points_of_interest, app.distance_matrix)
        else:
            raise ValueError("Algoritmo no soportado")
        
        # Convertir nodos a coordenadas
        path_coordinates = []
        for node in path:
            if node in app.graph:
                path_coordinates.append(app.graph.nodes[node]['pos'])
            else:
                raise ValueError(f"Nodo {node} no encontrado en el grafo")
        
        return jsonify({
            "status": "success",
            "path": path,
            "distance": distance,
            "path_coordinates": path_coordinates,
            "path_geojson": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[coord[1], coord[0]] for coord in path_coordinates]
                }
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Crear archivos básicos si no existen
    if not os.path.exists('static/css/styles.css'):
        with open('static/css/styles.css', 'w') as f:
            f.write("""body { font-family: Arial; margin: 0; padding: 20px; }""")
    
    if not os.path.exists('static/js/app.js'):
        with open('static/js/app.js', 'w') as f:
            f.write("// Tu código frontend aquí")
    
    app.run(host='0.0.0.0', port=5001, debug=True)