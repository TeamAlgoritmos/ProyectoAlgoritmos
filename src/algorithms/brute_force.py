import networkx as nx
from itertools import permutations
import random

def solve(graph, points):
    """Solución por fuerza bruta para TSP con ≤ 5 puntos aleatorios"""
    
    if len(points) > 10:
        sampled_points = random.sample(points, 5)
    else:
        sampled_points = points

    min_path = None
    min_distance = float('inf')
    
    # Intentar todas las permutaciones posibles (ciclo)
    for perm in permutations(sampled_points[1:]):
        current_path = [sampled_points[0]] + list(perm) + [sampled_points[0]]

        try:
            current_distance = sum(
                nx.shortest_path_length(graph, current_path[i], current_path[i+1], weight='weight')
                for i in range(len(current_path) - 1)
            )

            if current_distance < min_distance:
                min_distance = current_distance
                min_path = current_path
        except nx.NetworkXNoPath:
            continue

    if min_path is None:
        raise ValueError("No se encontró una ruta válida entre los puntos.")

    return min_path, min_distance
