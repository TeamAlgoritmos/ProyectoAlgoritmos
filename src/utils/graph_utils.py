import networkx as nx

def calculate_shortest_path_distance(graph, node_a, node_b):
    """
    Calcula la distancia del camino más corto entre dos nodos en el grafo.
    
    Args:
        graph: Grafo NetworkX
        node_a: Nodo de inicio
        node_b: Nodo de destino
    
    Returns:
        float: Distancia del camino más corto
    """
    try:
        return nx.shortest_path_length(graph, source=node_a, target=node_b, weight='weight')
    except nx.NetworkXNoPath:
        return float('inf')

def create_graph_from_data(df):
    """Crea un grafo NetworkX desde DataFrame"""
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row['origen'], row['destino'], weight=row['distancia'])
    return G

def add_point_to_graph(G, point_id, lat, lon):
    """Añade un punto al grafo (versión simplificada)"""
    # Implementación básica - puedes mejorarla después
    G.add_node(point_id, pos=(lat, lon))
    return G