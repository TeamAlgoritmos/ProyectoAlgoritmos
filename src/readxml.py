import xml.etree.ElementTree as ET

# ---------------------
# Definición de clases
# ---------------------

class Nodo:
    def __init__(self, id, lon, lat, visible=True, version="1"):
        self.id = id
        self.lon = float(lon)
        self.lat = float(lat)
        self.visible = visible
        self.version = version

    def __repr__(self):
        return f"Nodo(id={self.id}, lat={self.lat}, lon={self.lon})"

class Camino:
    def __init__(self, id, nodos=None, visible=True, version="1"):
        self.id = id
        self.nodos = nodos if nodos else []
        self.visible = visible
        self.version = version

    def __repr__(self):
        return f"Camino(id={self.id}, nodos={self.nodos})"

# ---------------------
# Lógica para procesar el XML
# ---------------------

def procesar_mapa(archivo_xml):
    nodos = {}
    caminos = []
    mapa_nodo_a_caminos = {}

    tree = ET.parse(archivo_xml)
    root = tree.getroot()

    for node in root.findall('node'):
        id = node.get('id')
        lon = node.get('lon')
        lat = node.get('lat')
        visible = node.get('visible', 'true') == 'true'
        version = node.get('version', '1')
        nodo_obj = Nodo(id, lon, lat, visible, version)
        nodos[id] = nodo_obj

    for way in root.findall('way'):
        id = way.get('id')
        visible = way.get('visible', 'true') == 'true'
        version = way.get('version', '1')
        refs = [nd.get('ref') for nd in way.findall('nd')]

        camino_obj = Camino(id, refs, visible, version)
        caminos.append(camino_obj)

        for ref in refs:
            if ref in mapa_nodo_a_caminos:
                mapa_nodo_a_caminos[ref].append(camino_obj)
            else:
                mapa_nodo_a_caminos[ref] = [camino_obj]

    return nodos, caminos, mapa_nodo_a_caminos


if __name__ == "__main__":
    print("hola mundo")
    archivo = "prueba/nodes+ways.xml"
    
    nodos, caminos, mapa = procesar_mapa(archivo)

    print("NODOS:")
    for nodo in nodos.values():
        print(nodo)

    print("\nCAMINOS:")
    for camino in caminos:
        print(camino)

    print("\nMAPA NODO -> CAMINOS:")
    for nodo_id, lista_caminos in mapa.items():
        print(f"Nodo {nodo_id} -> {lista_caminos}")

