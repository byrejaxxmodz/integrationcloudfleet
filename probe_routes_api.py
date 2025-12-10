
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("CLOUDFLEET_API_URL")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN")

if not API_URL:
    print("API_URL not set")
    exit()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def probe_routes():
    print(f"I: Probing {API_URL}routes")
    
    # 1. No Params
    try:
        r = requests.get(f"{API_URL}routes", headers=HEADERS)
        print(f"GET /routes (No params): {r.status_code}")
        if r.status_code == 200:
            print("  Example:", r.json()[:1])
    except Exception as e:
        print(f"  Error: {e}")

    # 2. With Customer ID 1 (CCM PRAXAIR)
    try:
        r = requests.get(f"{API_URL}routes?customerId=1", headers=HEADERS)
        print(f"GET /routes?customerId=1: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Count: {len(data)}")
            # Check for PRU-PRU
            found = [x for x in data if "PRU" in str(x.get("code") or "").upper()]
            if found:
                print("  FOUND PRU-PRU in API!")
                print(json.dumps(found[0], indent=2))
            else:
                print("  PRU-PRU NOT found in API response for ID 1")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    probe_routes()
