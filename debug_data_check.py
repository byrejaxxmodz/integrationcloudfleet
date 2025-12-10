
import asyncio
import os
from dotenv import load_dotenv
import logging
from app.cloudfleet import get_camiones, get_clientes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def inspect_vehicle_and_clients():
    try:
        # 1. Fetch all vehicles and find FKL92H
        print("--- SEARCHING FOR FKL92H ---")
        vehiculos = get_camiones()
        target_veh = None
        for v in vehiculos:
            code = v.get("code") or ""
            if "FKL" in code and "92" in code: # Fuzzy matching or exact FKL92H
                 target_veh = v
                 print(f"FOUND VEHICLE: {code}")
                 print(f"  ID: {v.get('id')}")
                 print(f"  Tipo: {v.get('typeName')}")
                 print(f"  Centro Costo: {v.get('costCenter')}")
                 print(f"  Cliente ID (Direct): {v.get('customerId')}")
                 print(f"  City: {v.get('city')}")
                 break
        
        if not target_veh:
            print("Vehicle FKL92H not found in get_camiones()")

        # 2. Fetch Clients to see if 'generico' exists
        print("\n--- CHECKING CLIENTS ---")
        clientes = get_clientes()
        for c in clientes:
            nombre = c.get("nombre", c.get("name", "")).lower()
            if "generico" in nombre or "ccm" in nombre:
                print(f"Valid Client Found: {c.get('nombre')} (ID: {c.get('id')})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_vehicle_and_clients()
