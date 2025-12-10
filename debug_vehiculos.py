
import requests
import json

def debug_vehiculos():
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- SEDE RESOLUTION ---\n")
        try:
            r_sedes = requests.get('http://localhost:8000/sedes')
            sedes = r_sedes.json()
            match = next((s for s in sedes if 'TOCANCIPA' in (s.get('name') or '').upper() or 'TOCANCIPA' in (s.get('city') or '').upper()), None)
            
            if match:
                f.write(f"Match Found:\n")
                f.write(f"  ID: {match.get('id')}\n")
                f.write(f"  Name: '{match.get('name')}'\n")
                f.write(f"  City: '{match.get('city')}'\n") # This is crucial
            else:
                f.write("No Sede found for TOCANCIPA\n")

            f.write("\n--- VEHICLE LOOKUP ---\n")
            # Mimic Frontend: if Match found, use its city or name
            search_city = "TOCANCIPA"
            if match:
                search_city = match.get('city') or match.get('name')
            
            f.write(f"Searching Vehicles with ciudad='{search_city}'...\n")
            r_v = requests.get(f"http://localhost:8000/vehiculos?ciudad={search_city}")
            vehs = r_v.json()
            f.write(f"Count: {len(vehs)}\n")
            if len(vehs) > 0:
                f.write(f"First Vehicle:\n")
                f.write(f"  Ubicacion: '{vehs[0].get('ubicacion_ciudad')}'\n")
                f.write(f"  Raw City: {vehs[0].get('datos_adicionales', {}).get('city')}\n")
                f.write(f"  Customer ID: {vehs[0].get('datos_adicionales', {}).get('customerId')}\n")
                f.write(f"  Cliente Param: {vehs[0].get('datos_adicionales', {}).get('cliente_id')}\n")
                f.write(f"  Cost Center: {vehs[0].get('datos_adicionales', {}).get('costCenter')}\n")


        except Exception as e:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    debug_vehiculos()
