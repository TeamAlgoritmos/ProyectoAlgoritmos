import networkx as nx

def solve(graph, points):
    """Versión tolerante a desconexiones"""
    if len(points) < 2:
        return points, float('inf')
    
    path = [points[0]]
    unvisited = set(points[1:])
    
    while unvisited:
        current = path[-1]
        reachable = [n for n in unvisited if nx.has_path(graph, current, n)]
        
        if not reachable:
            break  # No hay más nodos alcanzables
            
        nearest = min(reachable, 
                     key=lambda x: nx.shortest_path_length(graph, current, x, weight='weight'))
        path.append(nearest)
        unvisited.remove(nearest)
    
    # Intentar cerrar el ciclo si es posible
    if len(path) > 2 and path[0] != path[-1]:
        if nx.has_path(graph, path[-1], path[0]):
            path.append(path[0])
    
    # Calcular distancia total (infinito si hay desconexiones)
    total_distance = 0
    for i in range(len(path)-1):
        try:
            total_distance += nx.shortest_path_length(graph, path[i], path[i+1], weight='weight')
        except nx.NetworkXNoPath:
            return path, float('inf')
    
    return path, total_distance