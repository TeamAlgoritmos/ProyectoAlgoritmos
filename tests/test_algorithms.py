import pytest
import networkx as nx
import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms.brute_force import solve as brute_force_tsp
from src.algorithms.nearest_neighbor import solve as nearest_neighbor_tsp

class TestAlgorithms:
    @pytest.fixture
    def sample_graph(self):
        G = nx.Graph()
        G.add_edge('A', 'B', weight=1)
        G.add_edge('B', 'C', weight=1)
        G.add_edge('C', 'D', weight=1)
        G.add_edge('D', 'A', weight=1)
        G.add_edge('A', 'C', weight=1.5)
        G.add_edge('B', 'D', weight=1.5)
        return G

    def test_nearest_neighbor(self, sample_graph):
        path, distance = nearest_neighbor_tsp(sample_graph, 'A')
        assert len(path) == 5  # 4 nodos + regreso al inicio
        assert path[0] == 'A'
        assert path[-1] == 'A'
        assert distance > 0
        print(f"\nRuta del vecino más cercano: {path}")
        print(f"Distancia total: {distance}")

    def test_brute_force(self, sample_graph):
        path, distance = brute_force_tsp(sample_graph, 'A')
        assert len(path) == 5  # 4 nodos + regreso al inicio
        assert path[0] == 'A'
        assert path[-1] == 'A'
        assert distance > 0
        print(f"\nRuta de fuerza bruta: {path}")
        print(f"Distancia total: {distance}")

    def test_comparison(self, sample_graph):
        bf_path, bf_distance = brute_force_tsp(sample_graph, 'A')
        nn_path, nn_distance = nearest_neighbor_tsp(sample_graph, 'A')
        
        print("\nComparación de algoritmos:")
        print(f"Fuerza bruta - Ruta: {bf_path}, Distancia: {bf_distance}")
        print(f"Vecino más cercano - Ruta: {nn_path}, Distancia: {nn_distance}")
        
        # El algoritmo de fuerza bruta debe encontrar una distancia menor o igual
        assert bf_distance <= nn_distance