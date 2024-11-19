from geopy.distance import geodesic
import folium
import osmnx as ox
import networkx as nx

def find_approximate_route(start_coords, hospital_coords, hospital_names):
    # Crear el grafo centrado en el punto de inicio
    distancia_carga = 50000
    G = ox.graph_from_point(start_coords, dist=distancia_carga, network_type='drive')
    
    # Encontrar los nodos más cercanos para la ubicación de inicio y cada hospital
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    hospital_nodes = [ox.distance.nearest_nodes(G, coords[1], coords[0]) for coords in hospital_coords]

    # Inicializar variables para la ruta
    route = [start_node]
    ordered_hospital_coords = []
    ordered_hospital_names = []
    total_distance = 0
    current_node = start_node
    unvisited_nodes = set(hospital_nodes)

    # Algoritmo Vecino Más Cercano para encontrar una ruta más corta
    while unvisited_nodes:
        # Encontrar el nodo no visitado más cercano
        nearest_node = min(unvisited_nodes, key=lambda node: nx.shortest_path_length(G, current_node, node, weight="length"))
        
        # Actualizar la ruta y las listas con los nodos ordenados, nombres y coordenadas
        route.append(nearest_node)
        hospital_index = hospital_nodes.index(nearest_node)  # Obtener el índice original
        ordered_hospital_coords.append(hospital_coords[hospital_index])  # Coordenadas ordenadas
        ordered_hospital_names.append(hospital_names[hospital_index])    # Nombres ordenados
        
        # Actualizar la distancia y el nodo actual
        total_distance += nx.shortest_path_length(G, current_node, nearest_node, weight="length")
        current_node = nearest_node
        unvisited_nodes.remove(nearest_node)

    # Convertir los nodos de la ruta a coordenadas para el mapeo
    approximate_route_coords = []
    for i in range(len(route) - 1):
        path_nodes = nx.shortest_path(G, route[i], route[i + 1], weight='length')
        path_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path_nodes]
        approximate_route_coords.extend(path_coords)

    return G, approximate_route_coords, ordered_hospital_coords, ordered_hospital_names, total_distance

def generate_map(route_coords, start_coords, ordered_hospital_names, ordered_hospital_coords, output_path, start_name="Punto de inicio"):
    # Crear el mapa centrado en el punto de inicio
    map_obj = folium.Map(location=start_coords, zoom_start=12)
    
    # Agregar el marcador de la ubicación de inicio
    folium.Marker(
        location=start_coords,
        tooltip=f"Inicio: {start_name}",
        icon=folium.Icon(color="blue")
    ).add_to(map_obj)
    
    # Agregar los marcadores ordenados para cada hospital con el orden de visita
    for idx, (coords, name) in enumerate(zip(ordered_hospital_coords, ordered_hospital_names), start=1):
        folium.Marker(
            location=coords,
            tooltip=f"Destino {idx}: {name}",
            icon=folium.Icon(color="green")
        ).add_to(map_obj)
    
    # Graficar la ruta aproximada en el mapa
    folium.PolyLine(route_coords, color="red", weight=2.5, tooltip="Ruta aproximada").add_to(map_obj)

    # Guardar el mapa como un archivo HTML
    map_obj.save(output_path)
