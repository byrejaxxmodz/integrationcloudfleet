
import requests
import json

def debug_rutas():
    print("--- ROUTE DEBUGGING FOR TOCANCIPA ---")
    
    # 1. Fetch all routes for the client (assuming CCM PRAXAIR ID from debug_output.txt if available, or just filtering by city)
    # Validation showed CCM PRAXAIR ID is likely 1 or similar, but let's try searching by City first.
    
    print("\n1. Searching Routes with ciudad='TOCANCIPA' (Backend Filter)...")
    
    # FETCH CLIENT ID FIRST for proper simulation
    client_id = None
    try:
        clients = requests.get("http://localhost:8000/clientes").json()
        target = next((c for c in clients if "PRAXAIR" in c['nombre'].upper()), clients[0] if clients else None)
        if target:
            client_id = target['id']
            print(f"  Using Client: {target['nombre']} (ID: {client_id})")
    except:
        pass

    try:
        url = "http://localhost:8000/rutas_v2?ciudad=TOCANCIPA"
        if client_id:
            url += f"&cliente_id={client_id}"
            
        r = requests.get(url)

        rutas = r.json()
        print(f"Count: {len(rutas)}")
        for i, r in enumerate(rutas[:5]):
            print(f"  Ruta {i+1}:")
            print(f"    Code: {r.get('codigo')}")
            print(f"    Name: {r.get('nombre')}")
            print(f"    Origin: {r.get('origen')}")
            print(f"    Dest: {r.get('destino')}")
            print(f"    Via Code (prop): {r.get('via_codigo')}")
            print(f"    Vias (list): {r.get('vias')}")
            print(f"    Via Detalle: {r.get('vias_detalle')}")
    except Exception as e:
        print(f"Error fetching routes: {e}")

    # 2. Fetch ALL routes and check for Tocancipa in Origin/Dest (Frontend Simulation Logic)
    # We want to see if the Backend Filter misses some that the 'Smart Match' would find.
    print("\n2. Fetching ALL routes (limit 100) and manually matching 'TOCANCIPA'...")
    try:
        # We assume listing without filter returns many
        r_all = requests.get("http://localhost:8000/rutas_v2?limit=100") 
        start_rutas = r_all.json()
        
        matches = []
        for r in start_rutas:
            orig = str(r.get('origen') or '')
            dest = str(r.get('destino') or '')
            if 'TOCANCIPA' in orig.upper() or 'TOCANCIPA' in dest.upper():
                matches.append(r)
        
        print(f"Manual Match Count: {len(matches)}")
        if len(matches) > 0 and len(matches) != len(rutas):
            print("Difference detected! Logic mismatch.")
            
        for i, r in enumerate(matches[:5]):
             print(f"  Match {i+1} ({r.get('codigo')}): {r.get('origen')} -> {r.get('destino')} | Via: {r.get('via_codigo')}")

    except Exception as e:
        print(f"Error manual check: {e}")

if __name__ == "__main__":
    debug_rutas()
