import itertools
from typing import List, Tuple
import networkx as nx
import time

def solve(graph: nx.Graph, points: List[str], distance_matrix: dict) -> Tuple[List[str], float, float]:
    """
    Implementación del algoritmo de fuerza bruta para TSP.
    
    Args:
        graph: Grafo de NetworkX que representa la red de carreteras
        points: Lista de puntos a visitar
        distance_matrix: Matriz de distancias precalculada
        
    Returns:
        Tuple[List[str], float, float]: (ruta óptima, distancia total, tiempo de ejecución)
    """
    start_time = time.time()
    
    if not points:
        raise ValueError("No hay puntos para visitar")
    
    start_node = points[0]
    nodes = points[1:]  # Removemos el nodo inicial
    
    min_distance = float('inf')
    best_path = None
    
    # Generamos todas las permutaciones posibles
    for path in itertools.permutations(nodes):
        # Agregamos el nodo inicial al principio y al final
        current_path = [start_node] + list(path) + [start_node]
        
        # Calculamos la distancia total del camino usando la matriz de distancias
        distance = 0
        for i in range(len(current_path) - 1):
            try:
                distance += distance_matrix[current_path[i]][current_path[i + 1]]
            except KeyError:
                distance = float('inf')
                break
        
        # Actualizamos si encontramos un camino mejor
        if distance < min_distance:
            min_distance = distance
            best_path = current_path
    
    execution_time = time.time() - start_time
    return best_path, min_distance, execution_time
