
import logging
from app.cloudfleet import get_camiones, get_clientes

def inspect_vehicle_and_clients():
    try:
        # 1. Fetch all vehicles and find FKL92H
        print("SEARCHING_VEHICLE_START")
        vehiculos = get_camiones() or []
        target_veh = None
        for v in vehiculos:
            code = str(v.get("code") or "")
            if "FKL" in code: 
                 print(f"VEHICLE_FOUND: {code}")
                 cc = v.get("costCenter") or {}
                 if isinstance(cc, dict):
                    print(f"CC_NAME: {cc.get('name')}")
                    print(f"CC_CODE: {cc.get('code')}")
                    print(f"CC_ID: {cc.get('id')}")
                 else:
                    print(f"CC_RAW: {cc}")
                 print(f"CLIENT_ID: {v.get('customerId')}")
        print("SEARCHING_VEHICLE_END")

        # 2. Fetch Clients
        print("SEARCHING_CLIENTS_START")
        clientes = get_clientes() or []
        for c in clientes:
            print(f"CLIENT: {c.get('name') or c.get('nombre')} ID: {c.get('id')}")
        print("SEARCHING_CLIENTS_END")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    inspect_vehicle_and_clients()
