import random
import networkx as nx
from math import exp

def solve(graph, points, population_size=10, generations=5, mutation_rate=0.05):
    """Algoritmo genético para TSP"""
    
    # Función de fitness (inversa de la distancia)
    def calculate_fitness(path):
        try:
            distance = sum(nx.shortest_path_length(graph, path[i], path[i+1], weight='weight') 
                         for i in range(len(path)-1))
            return 1 / (1 + distance)  # Evitar división por cero
        except nx.NetworkXNoPath:
            return 0
    
    # Operador de mutación (intercambio aleatorio)
    def mutate(path):
        if random.random() < mutation_rate and len(path) > 3:
            i, j = random.sample(range(1, len(path)-1), 2)
            path[i], path[j] = path[j], path[i]
        return path
    
    # Operador de cruce (OX1)
    def crossover(parent1, parent2):
        size = len(parent1)
        start, end = sorted(random.sample(range(1, size-1), 2))
        
        # Crear hijo con segmento de parent1
        child = [None]*size
        child[start:end] = parent1[start:end]
        
        # Rellenar con genes de parent2
        current_pos = end % size
        for gene in parent2[end:] + parent2[:end]:
            if gene not in child[start:end]:
                child[current_pos] = gene
                current_pos = (current_pos + 1) % size
        
        return child
    
    # Población inicial
    population = []
    for _ in range(population_size):
        path = points.copy()
        if len(path) > 2:
            # Mezclar puntos intermedios
            interior = path[1:-1]
            random.shuffle(interior)
            path[1:-1] = interior
        population.append(path)
    
    # Evolución
    for _ in range(generations):
        # Evaluar fitness
        population.sort(key=calculate_fitness, reverse=True)
        
        # Selección elitista (conservar los mejores)
        next_gen = population[:int(population_size*0.2)]
        
        # Reproducción
        while len(next_gen) < population_size:
            # Selección por torneo
            parent1 = max(random.sample(population, 3), key=calculate_fitness)
            parent2 = max(random.sample(population, 3), key=calculate_fitness)
            
            # Cruzamiento
            child = crossover(parent1, parent2)
            
            # Mutación
            child = mutate(child)
            
            next_gen.append(child)
        
        population = next_gen
    
    # Mejor solución encontrada
    best_path = max(population, key=calculate_fitness)
    best_distance = sum(nx.shortest_path_length(graph, best_path[i], best_path[i+1], weight='weight') 
                   for i in range(len(best_path)-1))
    
    return best_path, best_distance