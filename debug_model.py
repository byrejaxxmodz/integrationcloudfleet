import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

BASE_URL = os.getenv("CLOUDFLEET_API_URL", "https://fleet.cloudfleet.com/api/v1").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json"
    }

def probe_model():
    print(f"Base: {BASE_URL}")
    
    # 1. Inspect Routes
    print("\n--- Inspecting Routes ---")
    try:
        res = requests.get(f"{BASE_URL}/routes", headers=get_headers())
        if res.ok:
            data = res.json()
            items = data if isinstance(data, list) else data.get("items", [])
            print(f"Routes found: {len(items)}")
            if items:
                r = items[0]
                # print(json.dumps(r, indent=2)[:500])
                orig = r.get("origin")
                dest = r.get("destination")
                print(f"\nORIGIN: {orig}")
                print(f"DESTINATION: {dest}")
        else:
            print(f"Routes Error: {res.status_code} {res.text[:100]}")
    except Exception as e:
        print(f"Routes Ex: {e}")

    # 2. Inspect Vehicles (Skipped for brevity)
    # print("\n--- Inspecting Vehicles ---")
    pass

if __name__ == "__main__":
    probe_model()
