from typing import List, Tuple
import networkx as nx
import time

def solve(graph: nx.Graph, points: List[str], distance_matrix: dict) -> Tuple[List[str], float, float]:
    """
    Implementación del algoritmo del vecino más cercano para TSP.
    
    Args:
        graph: Grafo de NetworkX que representa la red de carreteras
        points: Lista de puntos a visitar
        distance_matrix: Matriz de distancias precalculada
        
    Returns:
        Tuple[List[str], float, float]: (ruta encontrada, distancia total, tiempo de ejecución)
    """
    start_time = time.time()
    
    if not points:
        raise ValueError("No hay puntos para visitar")
    
    start_node = points[0]
    unvisited = set(points[1:])  # Removemos el nodo inicial
    
    current = start_node
    path = [current]
    total_distance = 0
    
    while unvisited:
        # Encontrar el vecino más cercano no visitado
        min_distance = float('inf')
        next_node = None
        
        for node in unvisited:
            try:
                distance = distance_matrix[current][node]
                if distance < min_distance:
                    min_distance = distance
                    next_node = node
            except KeyError:
                continue
        
        if next_node is None:
            # No hay camino posible
            return None, float('inf'), time.time() - start_time
        
        # Actualizar el camino
        path.append(next_node)
        total_distance += min_distance
        unvisited.remove(next_node)
        current = next_node
    
    # Volver al nodo inicial
    try:
        final_distance = distance_matrix[current][start_node]
        total_distance += final_distance
        path.append(start_node)
    except KeyError:
        return None, float('inf'), time.time() - start_time
    
    execution_time = time.time() - start_time
    return path, total_distance, execution_time
