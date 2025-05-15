def encontrar_caminos(matriz_distancias, inicio='A', actual='A', camino=None, caminos=None, max_depth=10):
    if camino is None:
        camino = [inicio]
    if caminos is None:
        caminos = []
    
    # Evitar camino muy largo (opcional para evitar ciclos infinitos)
    if len(camino) > max_depth:
        return caminos
    
    # Si estamos en el nodo inicio, pero no es el primer paso, guardar el camino
    if actual == inicio and len(camino) > 1:
        caminos.append(camino.copy())
        # No retornamos acá porque puede haber caminos más largos, continuamos explorando
    
    # Explorar vecinos
    for vecino in matriz_distancias.get(actual, {}):
        # Agregar vecino al camino y continuar búsqueda
        camino.append(vecino)
        encontrar_caminos(matriz_distancias, inicio, vecino, camino, caminos, max_depth)
        camino.pop()  # backtrack
    
    return caminos


matriz_distancias = {
    'A': {'D': 21, 'E': 20, 'B': 8},
    'D': {'A': 21, 'E': 7, 'B': 15},
    'E': {'A': 20, 'D': 7, 'B': 15},
    'B': {'A': 8, 'D': 15, 'E': 15}
}

caminos = encontrar_caminos(matriz_distancias, max_depth=6)
for c in caminos:
    print(c)