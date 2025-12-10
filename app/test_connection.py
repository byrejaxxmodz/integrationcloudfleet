import os
import sys

# Load env vars manually for the script since dot-env might not be auto-loaded without library
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ[key] = val

from app.cloudfleet import get_clientes, get_camiones

try:
    print("Testing CloudFleet Connection...")
    print(f"URL: {os.getenv('CLOUDFLEET_API_URL')}")
    
    # Test 1: Customers
    print("\nfetching Customers...")
    clientes = get_clientes()
    print(f"Found {len(clientes)} customers.")
    if clientes:
        print(f"First Customer: {clientes[0].get('name')}")

    # Test 2: Vehicles (limit paging)
    print("\nFetching Vehicles (first page)...")
    os.environ["CLOUDFLEET_MAX_PAGES"] = "1"
    camiones = get_camiones()
    print(f"Found {len(camiones)} vehicles in first page.")
    if camiones:
        print(f"First Vehicle: {camiones[0].get('code')}")

    print("\nConnection Successful!")

except Exception as e:
    print(f"\nConnection Failed: {e}")
