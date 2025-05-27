import requests
import urllib.parse
import math

# -- Constantes --
route_url = "https://graphhopper.com/api/1/route?"
geocode_url = "https://graphhopper.com/api/1/geocode?"
# Reemplaza con tu clave GraphHopper API. ¡Recuerda mantenerla segura en producción!
key = "0d29af59-03f1-438a-a8c0-cd49d6de4fee"

# Rendimiento promedio del vehículo (km por litro). Ajusta esto según tus necesidades.
FUEL_CONSUMPTION_KM_PER_LITER = 12.0 # Ejemplo: 12 km/litro para un coche

def geocoding (location, api_key):
    """
    Realiza la geocodificación de una localización utilizando la API de GraphHopper.
    """
    while location.strip() == "":
        location = input("Localización no puede estar vacía. Ingrese nuevamente la localización: ").strip()

    url = geocode_url + urllib.parse.urlencode({"q":location, "limit": "1", "key":api_key})

    json_status = 0
    lat = "null"
    lng = "null"
    new_loc = location

    try:
        replydata = requests.get(url, timeout=10)
        replydata.raise_for_status()
        json_status = replydata.status_code
        json_data = replydata.json()

        if len(json_data["hits"]) != 0:
            lat = (json_data["hits"][0]["point"]["lat"])
            lng = (json_data["hits"][0]["point"]["lng"])
            name = json_data["hits"][0]["name"]
            value = json_data["hits"][0]["osm_value"]

            country = json_data["hits"][0].get("country", "")
            state = json_data["hits"][0].get("state", "")

            parts = [name]
            if state and state.lower() != name.lower():
                parts.append(state)
            if country and country.lower() != state.lower() and country.lower() != name.lower():
                parts.append(country)
            new_loc = ", ".join(parts)

            print(f"\nAPI URL para {new_loc} (Tipo de Localización: {value}):\n{url}")
        else:
            print(f">> Advertencia: No se encontraron resultados para la localización: '{location}'.")
    except requests.exceptions.HTTPError as errh:
        print(f">> Error HTTP en Geocodificación: {errh.response.status_code} - {errh.response.text if errh.response is not None else 'No response body'}")
        json_status = errh.response.status_code if errh.response is not None else 0
    except requests.exceptions.ConnectionError as errc:
        print(f">> Error de Conexión en Geocodificación: {errc} - No se pudo conectar a la API.")
        json_status = 0
    except requests.exceptions.Timeout as errt:
        print(f">> Tiempo de Espera Excedido en Geocodificación: {errt} - La solicitud a la API tardó demasiado.")
        json_status = 0
    except requests.exceptions.RequestException as err:
        print(f">> Error General de Solicitud en Geocodificación: {err}")
        json_status = 0
    except ValueError:
        print(f">> Error: La respuesta de la API de Geocodificación no es un JSON válido para '{location}'.")
        json_status = 0
    
    return json_status, lat, lng, new_loc

# --- Bucle Principal del Programa ---
while True:
    print("\n" + "="*60)
    print("        Bienvenido al Planificador de Viajes GraphHopper")
    print("="*60)
    print("Perfil del vehículo disponible:")
    print("  - car (coche)")
    print("  - bike (bicicleta)")
    print("  - foot (a pie)")
    print("  (Escriba 'q' o 'quit' en cualquier momento para salir del programa)")
    print("="*60)

    profile_options = ["car", "bike", "foot"]
    vehicle = input("Ingrese uno de los perfiles de transporte de la lista: ").lower().strip()

    if vehicle in ["quit", "q"]:
        print("Saliendo del programa. ¡Hasta luego!")
        break

    elif vehicle not in profile_options:
        vehicle = "car" # Se establece a 'car' si no es válido
        print(">> Advertencia: Perfil no válido ingresado. Usando el perfil 'car' por defecto.")

    # --- Localización de Origen ---
    loc1 = input("Ingrese la Localización de Inicio (ej. Santiago, Chile): ").strip()
    if loc1.lower() in ["quit", "q"]:
        print("Saliendo del programa. ¡Hasta luego!")
        break
    
    orig_status, orig_lat, orig_lng, orig_name = geocoding(loc1, key)

    if orig_status != 200 or orig_lat == "null":
        print(f">> No se pudo obtener la ubicación de inicio para '{loc1}'. Reiniciando la entrada.")
        continue

    # --- Localización de Destino ---
    loc2 = input("Ingrese la Localización de Destino (ej. Valparaiso, Chile): ").strip()
    if loc2.lower() in ["quit", "q"]:
        print("Saliendo del programa. ¡Hasta luego!")
        break
    
    dest_status, dest_lat, dest_lng, dest_name = geocoding(loc2, key)

    if dest_status != 200 or dest_lat == "null":
        print(f">> No se pudo obtener la ubicación de destino para '{loc2}'. Reiniciando la entrada.")
        continue

    print("\n" + "="*60)
    print("        Calculando la Ruta...")
    print("="*60)

    params = {
        "key": key,
        "vehicle": vehicle,
        "point": [f"{orig_lat},{orig_lng}", f"{dest_lat},{dest_lng}"]
    }
    paths_url = route_url + urllib.parse.urlencode(params, doseq=True)

    try:
        paths_reply = requests.get(paths_url, timeout=15)
        paths_reply.raise_for_status()
        paths_status = paths_reply.status_code
        paths_data = paths_reply.json()

        print(f"Estado de la API de enrutamiento: {paths_status}")
        # print(f"URL de la API de enrutamiento:\n{paths_url}")
        print("="*60)

        if paths_status == 200 and "paths" in paths_data and len(paths_data["paths"]) > 0:
            distance_meters = paths_data["paths"][0]["distance"]
            time_ms = paths_data["paths"][0]["time"]

            # --- Cálculos de Distancia y Tiempo ---
            distance_km = distance_meters / 1000.0
            distance_miles = distance_km / 1.609344

            total_seconds = int(time_ms / 1000)
            travel_hr = total_seconds // 3600
            travel_min = (total_seconds % 3600) // 60
            travel_sec = total_seconds % 60

            # --- Cálculo de Bencina Requerida ---
            liters_required = 0.0 # Siempre inicializar a 0.0
            if vehicle == "car" and FUEL_CONSUMPTION_KM_PER_LITER > 0:
                liters_required = distance_km / FUEL_CONSUMPTION_KM_PER_LITER
            
            # --- Narrativa del Viaje ---
            print(f"\n--- Narrativa del Viaje ---")
            print(f"¡Prepárate para un emocionante viaje desde **{orig_name}** hasta **{dest_name}**!")
            print(f"Modalidad de transporte seleccionada: **{vehicle.upper()}**.")
            print(f"Estimamos que recorrerás una distancia de **{distance_km:.2f} kilómetros** "
                  f"({distance_miles:.2f} millas).")
            print(f"El tiempo estimado total del viaje es de **{travel_hr:02d} horas, {travel_min:02d} minutos y {travel_sec:02d} segundos**.")

            # *** LA BENCINA SE IMPRIME AQUÍ SIEMPRE QUE EL VEHICLE SEA 'CAR' ***
            if vehicle == "car":
                print(f"Para completar este viaje en coche, necesitarás aproximadamente **{liters_required:.2f} litros de bencina**.")
            elif vehicle == "bike":
                print("¡Un viaje ecológico en bicicleta! No se requiere bencina.")
            else: # foot
                print("¡Un viaje saludable a pie! No se requiere bencina.")

            print("\n--- Resumen Detallado de la Ruta ---")
            print(f"Origen: {orig_name}")
            print(f"Destino: {dest_name}")
            print(f"Perfil: {vehicle.upper()}")
            print(f"Distancia Total: {distance_km:.2f} km / {distance_miles:.2f} millas")
            print(f"Duración del Viaje: {travel_hr:02d}h {travel_min:02d}m {travel_sec:02d}s")
            
            # *** LA BENCINA SE IMPRIME TAMBIÉN AQUÍ SIEMPRE QUE EL VEHICLE SEA 'CAR' ***
            if vehicle == "car":
                print(f"Bencina Estimada: {liters_required:.2f} litros")
            
            print("="*60)

            print("\n--- Indicaciones Paso a Paso ---")
            if "instructions" in paths_data["paths"][0]:
                for i, instruction in enumerate(paths_data["paths"][0]["instructions"]):
                    path_text = instruction["text"]
                    instruction_distance_meters = instruction["distance"]
                    instruction_distance_km = instruction_distance_meters / 1000.0
                    instruction_distance_miles = instruction_distance_km / 1.609344

                    print(f"{i+1}. {path_text} ( {instruction_distance_km:.2f} km / {instruction_distance_miles:.2f} millas )")
            else:
                print("No se encontraron instrucciones detalladas para esta ruta.")
            print("="*60)

        else:
            print(">> Error: No se encontraron rutas válidas o hubo un problema en la respuesta de GraphHopper.")
            if "message" in paths_data:
                print(f"Mensaje de Error de la API: {paths_data['message']}")
            print("Por favor, verifique las localizaciones, el perfil del vehículo y su clave API.")
            print("*"*60)

    except requests.exceptions.HTTPError as errh:
        print(f">> Error HTTP al obtener la ruta: {errh.response.status_code} - {errh.response.text if errh.response is not None else 'No response body'}")
    except requests.exceptions.ConnectionError as errc:
        print(f">> Error de Conexión al obtener la ruta: {errc} - No se pudo conectar a la API de enrutamiento.")
    except requests.exceptions.Timeout as errt:
        print(f">> Tiempo de Espera Excedido al obtener la ruta: {errt} - La solicitud de enrutamiento tardó demasiado.")
    except requests.exceptions.RequestException as err:
        print(f">> Error General de Solicitud al obtener la ruta: {err}")
    except ValueError:
        print(f">> Error: La respuesta de la API de enrutamiento no es un JSON válido.")