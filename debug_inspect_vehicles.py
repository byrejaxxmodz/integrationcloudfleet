import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.cloudfleet import get_camiones

def debug_vehicles():
    print("=== DEBUG VEHICLES RAW ===")
    try:
        # Get 1 page
        camiones = get_camiones(max_pages=1)
        print(f"Total returned: {len(camiones)}")
        
        if camiones:
            # Print first 2
            for i, v in enumerate(camiones[:2]):
                print(f"\n--- Vehicle {i} ---")
                print(f"Code: {v.get('code')}")
                print(f"CustomerId (raw): {v.get('customerId')}")
                print(f"CostCenter: {json.dumps(v.get('costCenter'), indent=2)}")
                print(f"City: {json.dumps(v.get('city'), indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_vehicles()
