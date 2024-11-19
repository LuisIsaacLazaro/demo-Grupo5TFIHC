from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
from map_utils import find_approximate_route, generate_map

app = Flask(__name__)

# Ruta al archivo CSV
file_path = r"C:\Users\luisl\Downloads\CC184_TB2_u202323591_LazaroMachado_LuisIsaac\CC184_TB2_Cod_Ap_Nom\CODIGO FUENTE\TF - VERSION FINAL\TF - VERSION FINAL\DB_NO_VACIOS_LIMA.csv"
hospitals_df = pd.read_csv(file_path)

# Lista de hospitales seleccionados (vacía al inicio)
selected_hospitals = []

# Lista de localizaciones de inicio posibles
start_locations = [
    {"name": "Aeropuerto Jorge Chavez", "lat": -12.0396, "long": -77.10556},
    {"name": "Almacen Callao", "lat": -12.03121, "long": -77.09536},
    {"name": "Almacen Lurin", "lat": -12.29011, "long": -76.84078},
    {"name": "Puerto del Callao", "lat": -12.0469, "long": -77.1427}
]

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/select_hospitals", methods=["GET", "POST"])
def select_hospitals():
    global selected_hospitals
    if request.method == "POST":
        code = request.form.get("codigo_renaes")
        if code and code.isdigit():
            code = int(code)
            hospital = hospitals_df[hospitals_df['codigo_renaes'] == code]
            if not hospital.empty:
                hospital_coords = (hospital['latitud'].values[0], hospital['longitud'].values[0])
                hospital_name = hospital['nombre'].values[0]
                hospital_code = hospital['codigo_renaes'].values[0]
                if any(existing_code == hospital_code for _, _, existing_code in selected_hospitals):
                    return render_template("index.html", hospitals=selected_hospitals, error="Este hospital ya ha sido agregado.")
                selected_hospitals.append((hospital_coords, hospital_name, hospital_code))
            else:
                return render_template("index.html", hospitals=selected_hospitals, error="Código RENAES no encontrado")
    return render_template("index.html", hospitals=selected_hospitals)

@app.route("/generate_map", methods=["POST"])
def generate_map_route():
    global selected_hospitals
    if not selected_hospitals:
        return redirect(url_for("select_hospitals"))
    
    start_location_index = int(request.form.get("start_location"))
    start_location = start_locations[start_location_index]
    start_coords = (start_location['lat'], start_location['long'])
    start_name = start_location['name']
    
    hospital_coords = [coords for coords, _, _ in selected_hospitals]
    hospital_names = [name for _, name, _ in selected_hospitals]
    
    # Ensure hospital_coords are tuples (lat, long)
    hospital_coords = [(coords[0], coords[1]) for coords in hospital_coords]

    # Create 'static' directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Set the absolute path for hospital_route_map.html
    output_map_path = os.path.join(static_dir, 'hospital_route_map.html')
    
    # Use the approximate route function
    G, approximate_route, ordered_hospital_coords, ordered_hospital_names, total_distance = find_approximate_route(start_coords, hospital_coords, hospital_names)
    
    # Calcular el tiempo estimado (asumiendo una velocidad promedio de 60 km/h)
    average_speed_kmh = 60
    time_estimated_hours = total_distance / 1000 / average_speed_kmh
    time_estimated_minutes = time_estimated_hours * 60

    # Generar el mapa
    generate_map(approximate_route, start_coords, ordered_hospital_names, ordered_hospital_coords, output_map_path, start_name=start_name)
    
    # Pasar la información a la plantilla del mapa
    return render_template("map.html", 
                           total_distance=total_distance, 
                           time_estimated_minutes=int(time_estimated_minutes),
                           num_hospitals=len(selected_hospitals))

@app.route("/show_map")
def show_map():
    return render_template("map.html")

@app.route("/remove_hospital", methods=["POST"])
def remove_hospital():
    global selected_hospitals
    hospital_name = request.form.get("hospital_name")
    selected_hospitals = [
        (coords, name, code) for coords, name, code in selected_hospitals if name != hospital_name
    ]
    return redirect(url_for("select_hospitals"))

if __name__ == "__main__":
    app.run(debug=True)
