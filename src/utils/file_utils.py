import pandas as pd
import xml.etree.ElementTree as ET
from typing import Union

def load_network_data(filepath: str) -> Union[pd.DataFrame, dict]:
    """Carga datos de red vial desde CSV o XML"""
    if filepath.endswith('.xml'):
        return parse_osm_xml(filepath)
    else:
        return pd.read_csv(filepath)

def load_points_of_interest(filepath: str) -> pd.DataFrame:
    """Carga puntos de interés desde TSV o CSV"""
    if filepath.endswith('.tsv'):
        return pd.read_csv(filepath, sep='\t')
    return pd.read_csv(filepath)

def parse_osm_xml(filepath: str) -> dict:
    """Procesa archivo OSM XML y devuelve estructura con nodos y caminos"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    nodes = {}
    ways = []
    
    for node in root.findall('node'):
        nodes[node.get('id')] = {
            'lat': float(node.get('lat')),
            'lon': float(node.get('lon'))
        }
    
    for way in root.findall('way'):
        way_nodes = [nd.get('ref') for nd in way.findall('nd')]
        ways.append(way_nodes)
    
    return {'nodes': nodes, 'ways': ways}