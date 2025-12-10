
import requests
import json

def debug_rutas():
    # Try searching for something that might match "PLANTA CHILCO CAZUCA"
    # Maybe by city or just list all and filter locally to see what we get
    url = "http://localhost:8000/rutas_v2"
    print(f"Querying {url}...")
    try:
        resp = requests.get(url) # Get all routes first to see structure
        if resp.status_code == 200:
            data = resp.json()
            print(f"Got {len(data)} routes.")
            if data:
                # Print the first item to see structure
                print("Sample Route JSON:")
                print(json.dumps(data[0], indent=2))
                
                # Check for specific ones
                matches = [r for r in data if "CHILCO" in (r.get('nombre') or "").upper() or "CAZUCA" in (r.get('nombre') or "").upper()]
                print(f"Found {len(matches)} matches for CHILCO/CAZUCA")
                for m in matches[:3]:
                    print(json.dumps(m, indent=2))
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_rutas()
