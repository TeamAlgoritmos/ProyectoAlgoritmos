import os
import math
import time
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple
from algorithms import brute_force_solve, nearest_neighbor_solve, genetic_solve

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Variables globales
app.graph: Optional[nx.Graph] = None
app.points_of_interest: List[str] = []
app.node_coords: Dict[str, Tuple[float, float]] = {}

# ------------------------------------------
# Funciones de utilidad mejoradas
# ------------------------------------------


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en metros entre coordenadas geográficas (versión optimizada)"""
    R = 6_371_000  # Radio de la Tierra en metros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_xml(filepath: str) -> Dict:
    """Procesa archivos OSM XML con manejo de memoria eficiente"""
    print(f"Procesando archivo OSM: {filepath}")
    nodes = {}
    connections = []

    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start" and elem.tag == "node":
                try:
                    nodes[elem.get("id")] = {
                        "lat": float(elem.get("lat")),
                        "lon": float(elem.get("lon")),
                    }
                except (TypeError, ValueError):
                    continue

            elif event == "end" and elem.tag == "way":
                way_nodes = []
                for nd in elem.findall("nd"):
                    if nd.get("ref") in nodes:
                        way_nodes.append(nd.get("ref"))
                # Crear conexiones bidireccionales
                for i in range(len(way_nodes) - 1):
                    connections.append((way_nodes[i], way_nodes[i + 1]))
                    connections.append(
                        (way_nodes[i + 1], way_nodes[i])
                    )  # Conexión inversa
                elem.clear()

        return {
            "nodes": nodes,
            "connections": connections,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(connections)
                // 2,  # Divide por 2 por las conexiones bidireccionales
            },
        }
    except ET.ParseError as e:
        raise ValueError(f"Error en el formato XML: {str(e)}")


def create_graph(nodes: Dict, connections: List) -> nx.Graph:
    """Crea grafo NetworkX asegurando conectividad"""
    G = nx.Graph()

    # Añadir nodos con atributos de posición
    for node_id, coords in nodes.items():
        G.add_node(node_id, pos=(coords["lat"], coords["lon"]))
        app.node_coords[node_id] = (coords["lat"], coords["lon"])

    # Añadir aristas con distancias calculadas
    added_edges = set()
    for source, target in connections:
        if (source, target) not in added_edges and (target, source) not in added_edges:
            if source in nodes and target in nodes:
                distance = haversine_distance(
                    nodes[source]["lat"],
                    nodes[source]["lon"],
                    nodes[target]["lat"],
                    nodes[target]["lon"],
                )
                G.add_edge(source, target, weight=distance)
                added_edges.add((source, target))

    # Verificar y solucionar desconexiones
    if not nx.is_connected(G):
        print("Advertencia: Grafo no conectado. Conectando componentes...")
        connect_components(G)

    return G


def connect_components(graph):
    """Conecta componentes desconectados del grafo"""
    components = list(nx.connected_components(graph))
    while len(components) > 1:
        c1 = components.pop()
        c2 = components.pop()

        # Encontrar el par de nodos más cercano entre componentes
        min_dist = float("inf")
        best_pair = None

        for node1 in c1:
            for node2 in c2:
                pos1 = graph.nodes[node1]["pos"]
                pos2 = graph.nodes[node2]["pos"]
                dist = haversine_distance(*pos1, *pos2)
                if dist < min_dist:
                    min_dist = dist
                    best_pair = (node1, node2)

        # Añadir arista de conexión
        if best_pair:
            graph.add_edge(best_pair[0], best_pair[1], weight=min_dist)
            print(
                f"Conectados {best_pair[0]} y {best_pair[1]} (distancia: {min_dist:.2f}m)"
            )

        # Actualizar componentes
        components.append(c1.union(c2))


# ------------------------------------------
# Endpoints de la API mejorados
# ------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/api/load_network", methods=["POST"])
def load_network():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".xml"):
            return jsonify({"error": "Solo se aceptan archivos XML (formato OSM)"}), 400

        temp_path = f"temp_network_{time.time()}.xml"
        file.save(temp_path)

        try:
            xml_data = parse_xml(temp_path)
            app.graph = create_graph(xml_data["nodes"], xml_data["connections"])

            return jsonify(
                {
                    "status": "success",
                    "message": "Red vial cargada correctamente",
                    "stats": {
                        "nodes": len(app.graph.nodes()),
                        "edges": len(app.graph.edges()),
                        "connected": nx.is_connected(app.graph),
                    },
                    "visualization_data": {
                        "edges": [
                            {
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": [
                                        [
                                            app.graph.nodes[n1]["pos"][1],
                                            app.graph.nodes[n1]["pos"][0],
                                        ],
                                        [
                                            app.graph.nodes[n2]["pos"][1],
                                            app.graph.nodes[n2]["pos"][0],
                                        ],
                                    ],
                                },
                                "properties": {"color": "#cccccc", "weight": 2},
                            }
                            for n1, n2 in app.graph.edges()
                        ]
                    },
                }
            )

        finally:
            try:
                os.remove(temp_path)
            except:
                pass

    except Exception as e:
        return jsonify({"error": str(e), "type": "network_load_error"}), 500


@app.route("/api/load_points", methods=["POST"])
def load_points():
    try:
        if not app.graph:
            return jsonify({"error": "Primero cargue la red vial"}), 400

        if "file" not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files["file"]

        # Leer el contenido del archivo como texto
        content = file.read().decode("utf-8").splitlines()

        # Procesar manualmente el TSV
        points_data = []
        header = []
        for i, line in enumerate(content):
            # Saltar líneas vacías
            if not line.strip():
                continue

            # Dividir por tabs y limpiar espacios
            parts = [part.strip() for part in line.split("\t") if part.strip()]

            if i == 0:  # Encabezado
                header = [part.lower() for part in parts]
                if not all(col in header for col in ["x", "y", "id"]):
                    return (
                        jsonify(
                            {
                                "error": "El archivo debe contener columnas: X, Y, id",
                                "columnas_encontradas": header,
                            }
                        ),
                        400,
                    )
            else:  # Datos
                if len(parts) >= 3:
                    points_data.append(
                        {"lon": parts[0], "lat": parts[1], "id": parts[2]}
                    )

        # Validar que hay datos
        if not points_data:
            return jsonify({"error": "El archivo no contiene datos válidos"}), 400

        # Procesar puntos
        points = []
        problematic_points = []

        for item in points_data:
            try:
                # Convertir a float y validar
                lon = float(item["lon"])
                lat = float(item["lat"])
                point_id = item["id"]

                if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                    raise ValueError("Coordenadas fuera de rango")

                # Encontrar nodo más cercano
                closest_node = min(
                    app.graph.nodes(),
                    key=lambda n: haversine_distance(
                        lat,
                        lon,
                        app.graph.nodes[n]["pos"][0],
                        app.graph.nodes[n]["pos"][1],
                    ),
                )
                points.append(closest_node)

            except Exception as e:
                problematic_points.append(
                    {
                        "id": item.get("id", "N/A"),
                        "error": str(e),
                        "coordenadas": f"{item.get('lon', 'N/A')}, {item.get('lat', 'N/A')}",
                    }
                )
                continue

        if len(points) < 2:
            return (
                jsonify(
                    {
                        "error": "Se necesitan al menos 2 puntos válidos",
                        "puntos_cargados": len(points),
                        "errores": problematic_points,
                    }
                ),
                400,
            )

        # Verificar conectividad
        connectivity_issues = []
        for i in range(len(points) - 1):
            if not nx.has_path(app.graph, points[i], points[i + 1]):
                pos1 = app.graph.nodes[points[i]]["pos"]
                pos2 = app.graph.nodes[points[i + 1]]["pos"]
                connectivity_issues.append(
                    {
                        "from": points[i],
                        "to": points[i + 1],
                        "distance": haversine_distance(*pos1, *pos2),
                    }
                )

        if connectivity_issues:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Problemas de conectividad entre puntos",
                        "issues": connectivity_issues,
                    }
                ),
                400,
            )

        app.points_of_interest = points

        return jsonify(
            {
                "status": "success",
                "points_loaded": len(points),
                "sample_points": points[:5],
                "warnings": problematic_points if problematic_points else None,
                "visualization_data": [
                    {
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                app.graph.nodes[node]["pos"][1],
                                app.graph.nodes[node]["pos"][0],
                            ],
                        },
                        "properties": {
                            "popup": f"Punto {i+1}",
                            "color": "#e74c3c",
                            "radius": 6,
                        },
                    }
                    for i, node in enumerate(points)
                ],
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error inesperado: {str(e)}",
                    "type": "load_points_error",
                }
            ),
            500,
        )


def check_connectivity(graph, points):
    """Verifica conectividad entre todos los puntos"""
    issues = []
    for i in range(len(points) - 1):
        if not nx.has_path(graph, points[i], points[i + 1]):
            pos1 = graph.nodes[points[i]]["pos"][::-1]  # [lon, lat]
            pos2 = graph.nodes[points[i + 1]]["pos"][::-1]
            issues.append(
                {
                    "from": points[i],
                    "to": points[i + 1],
                    "from_coords": pos1,
                    "to_coords": pos2,
                    "distance_km": haversine_distance(*pos1[::-1], *pos2[::-1]) / 1000,
                }
            )
    return issues


@app.route("/api/solve_tsp", methods=["POST"])
def solve_tsp():
    try:
        if not app.graph:
            raise ValueError("Red vial no cargada")
        if not app.points_of_interest or len(app.points_of_interest) < 2:
            raise ValueError("Se necesitan al menos 2 puntos de interés")

        data = request.get_json()
        algorithm = data.get("algorithm", "").lower()
        points = app.points_of_interest

        # Verificación adicional de conectividad
        unreachable_pairs = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                if not nx.has_path(app.graph, points[i], points[j]):
                    unreachable_pairs.append((points[i], points[j]))

        if unreachable_pairs:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Problemas de conectividad detectados",
                        "unreachable_pairs": unreachable_pairs,
                        "suggestion": "Verifique la red vial o reduzca los puntos de interés",
                    }
                ),
                400,
            )

        # Ejecutar algoritmo
        start_time = time.time()

        if algorithm == "brute_force":
            path, distance = brute_force_solve(app.graph, points)
        elif algorithm == "nearest_neighbor":
            path, distance = nearest_neighbor_solve(app.graph, points)
        elif algorithm == "genetic":
            path, distance = genetic_solve(
                app.graph,
                points,
                population_size=data.get("population_size", 50),
                generations=data.get("generations", 100),
                mutation_rate=data.get("mutation_rate", 0.05),
            )
        else:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")

        execution_time = time.time() - start_time

        # Convertir nodos a coordenadas
        path_coordinates = []
        for node in path:
            if node in app.graph.nodes:
                path_coordinates.append(app.graph.nodes[node]["pos"])
            else:
                raise ValueError(f"Nodo {node} no encontrado en el grafo")

        # Preparar datos para visualización
        visualization_data = {
            "network": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [
                                    app.graph.nodes[n1]["pos"][1],
                                    app.graph.nodes[n1]["pos"][0],
                                ],
                                [
                                    app.graph.nodes[n2]["pos"][1],
                                    app.graph.nodes[n2]["pos"][0],
                                ],
                            ],
                        },
                        "properties": {"color": "#cccccc", "weight": 2},
                    }
                    for n1, n2 in app.graph.edges()
                ],
            },
            "points": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                app.graph.nodes[node]["pos"][1],
                                app.graph.nodes[node]["pos"][0],
                            ],
                        },
                        "properties": {
                            "color": "#2ecc71" if i == 0 else "#e74c3c",
                            "popup": f"Punto {i+1}",
                            "radius": 8,
                        },
                    }
                    for i, node in enumerate(points)
                ],
            },
            "route": {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lat, lon in path_coordinates],
                },
                "properties": {"color": "#3498db", "weight": 5},
            },
        }

        # Calcular centro del mapa
        lats = [coord[0] for coord in path_coordinates]
        lons = [coord[1] for coord in path_coordinates]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]

        return jsonify(
            {
                "status": "success",
                "algorithm": algorithm,
                "path": path,
                "distance": distance,
                "execution_time": execution_time,
                "path_coordinates": path_coordinates,
                "visualization_data": visualization_data,
                "center": center,
                "stats": {
                    "nodes_visited": len(path),
                    "unique_nodes": len(set(path)),
                    "total_points": len(points),
                    "graph_nodes": len(app.graph.nodes()),
                    "graph_edges": len(app.graph.edges()),
                },
            }
        )

    except ValueError as e:
        return (
            jsonify({"status": "error", "message": str(e), "type": "validation_error"}),
            400,
        )
    except nx.NetworkXError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error de red: {str(e)}",
                    "type": "network_error",
                }
            ),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error inesperado: {str(e)}",
                    "type": "server_error",
                }
            ),
            500,
        )


if __name__ == "__main__":
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=True)
