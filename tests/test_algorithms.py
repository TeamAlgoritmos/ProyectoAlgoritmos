import pytest
import networkx as nx
from src.algorithms.nearest_neighbor import nearest_neighbor_tsp

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
        tour = nearest_neighbor_tsp(sample_graph, 'A')
        assert len(tour) == 5  # 4 nodos + regreso al inicio
        assert tour[0] == 'A'
        assert tour[-1] == 'A'