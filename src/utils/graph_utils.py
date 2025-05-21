import networkx as nx
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula distancia en metros entre coordenadas geográficas"""
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi/2)**2 + 
         math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def create_graph_from_data(data: Union[pd.DataFrame, dict]) -> nx.Graph:
    """Crea grafo desde DataFrame o datos OSM"""
    G = nx.Graph()
    
    if isinstance(data, pd.DataFrame):
        # Para datos CSV tradicionales
        for _, row in data.iterrows():
            G.add_edge(row['origen'], row['destino'], weight=row['distancia'])
    else:
        # Para datos OSM XML
        nodes = data['nodes']
        ways = data['ways']
        
        # Añadir nodos con atributos de posición
        for node_id, coords in nodes.items():
            G.add_node(node_id, pos=(coords['lat'], coords['lon']))
        
        # Añadir aristas con distancias calculadas
        for way in ways:
            for i in range(len(way)-1):
                node1 = way[i]
                node2 = way[i+1]
                
                if node1 in nodes and node2 in nodes:
                    pos1 = nodes[node1]
                    pos2 = nodes[node2]
                    distance = haversine_distance(
                        pos1['lat'], pos1['lon'],
                        pos2['lat'], pos2['lon']
                    )
                    G.add_edge(node1, node2, weight=distance)
    
    return G

def find_nearest_node(G: nx.Graph, lat: float, lon: float) -> str:
    """Encuentra el nodo más cercano a unas coordenadas dadas"""
    closest_node = None
    min_distance = float('inf')
    
    for node, data in G.nodes(data=True):
        node_lat, node_lon = data['pos']
        dist = haversine_distance(lat, lon, node_lat, node_lon)
        if dist < min_distance:
            min_distance = dist
            closest_node = node
    
    return closest_node