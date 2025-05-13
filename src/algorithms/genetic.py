from typing import List, Tuple
import networkx as nx
import random

"""
Modifiquen este entero es solo para que el codigfo pudiera correr, 
este algortimo no fucniona, es solo para que el codigo pudiera correr
Mira eso Simon este es el tuyo 
!!!!!
"""
def solve(graph: nx.Graph, start_node: int) -> Tuple[List[int], float]:
    """
    Implementación básica del algoritmo genético para TSP.
    
    Args:
        graph: Grafo de NetworkX que representa la red de carreteras
        start_node: Nodo inicial para comenzar el recorrido
        
    Returns:
        Tuple[List[int], float]: (ruta encontrada, distancia total)
    """
    nodes = list(graph.nodes())
    if start_node not in nodes:
        raise ValueError("El nodo inicial no está en el grafo")
    
    # Por ahora, simplemente devolvemos una ruta aleatoria
    # como placeholder hasta que implementemos el algoritmo completo
    nodes.remove(start_node)
    random.shuffle(nodes)
    path = [start_node] + nodes + [start_node]
    
    # Calculamos la distancia total
    total_distance = 0
    for i in range(len(path) - 1):
        try:
            total_distance += nx.shortest_path_length(graph, 
                                                    path[i], 
                                                    path[i + 1], 
                                                    weight='weight')
        except nx.NetworkXNoPath:
            return None, float('inf')
    
    return path, total_distance
