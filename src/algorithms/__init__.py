from .brute_force import solve as brute_force_solve
from .nearest_neighbor import solve as nearest_neighbor_solve
from .genetic import solve as genetic_solve

__all__ = ['brute_force_solve', 'nearest_neighbor_solve', 'genetic_solve']