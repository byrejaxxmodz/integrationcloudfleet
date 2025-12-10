
import requests
import json

def check_rutas_v2():
    try:
        # Simulate the call made by the frontend
        # Assuming user selected Client ID 1 (CCM PRAXAIR) or similar, and City Yumbo
        url = "http://127.0.0.1:8000/rutas_v2?ciudad=YUMBO"
        
        print(f"Requesting: {url}")
        res = requests.get(url)
        print(f"Status: {res.status_code}")
        
        data = res.json()
        print(f"Total routes: {len(data)}")
        
        found = False
        for r in data:
            if "PRU" in r.get("codigo", "").upper():
                print("FOUND PRU-PRU!")
                print(json.dumps(r, indent=2))
                found = True
                
        if not found:
            print("PRU-PRU NOT FOUND in response.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_rutas_v2()
