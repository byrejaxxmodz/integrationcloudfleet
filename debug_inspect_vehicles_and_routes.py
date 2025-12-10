import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.cloudfleet import get_camiones, get_rutas

def debug_clean():
    print("=== DEBUG CLEAN ===")
    
    # 1. Inspect Vehicle
    print("--- VEHICLE ---")
    try:
        camiones = get_camiones(max_pages=1)
        if camiones:
            v = camiones[0]
            print(f"Code: {v.get('code')}")
            print(f"CustomerId: {v.get('customerId')}")  # Expecting None/Null if hypothesis matches
            print(f"CostCenter: {v.get('costCenter')}") 
    except Exception as e:
        print(f"Error vehicles: {e}")

    # 2. Inspect Route (fetch ANY route)
    print("\n--- ROUTE ---")
    try:
        # Get routes without client filter
        rutas = get_rutas(max_pages=1)
        if rutas:
            r = rutas[0]
            print(f"Code: {r.get('code')}")
            print(f"CustomerId: {r.get('customerId')}")
            print(f"LocationId: {r.get('locationId')}")
            # Check if there is any cost center info in route
            print(f"CostCenter (check): {r.get('costCenter')}")
            print(f"Keys: {list(r.keys())}")
        else:
            print("No routes found (global search).")
            
    except Exception as e:
        print(f"Error routes: {e}")

if __name__ == "__main__":
    debug_clean()
