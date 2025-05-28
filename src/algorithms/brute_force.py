import networkx as nx
from itertools import permutations

def solve(graph, points):
    """Solución por fuerza bruta para TSP (≤ 10 puntos)"""
    if len(points) > 10:
        raise ValueError("Demasiados puntos para fuerza bruta (max 10)")
    
    min_path = None
    min_distance = float('inf')
    
    # Puntos interiores (excluyendo inicio y fin si son iguales)
    interior_points = points[1:-1] if points[0] == points[-1] else points[1:]
    
    for perm in permutations(interior_points):
        current_path = [points[0]] + list(perm)
        if points[0] != points[-1]:
            current_path.append(points[-1])
        
        try:
            current_distance = sum(nx.shortest_path_length(graph, current_path[i], current_path[i+1], weight='weight') 
                                for i in range(len(current_path)-1))
            
            if current_distance < min_distance:
                min_distance = current_distance
                min_path = current_path
        except nx.NetworkXNoPath:
            continue
    
    return min_path, min_distance