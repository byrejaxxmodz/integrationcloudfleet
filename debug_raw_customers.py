import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CLOUDFLEET_API_URL", "https://fleet.cloudfleet.com/api/v1").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")

def debug_customers():
    endpoints = ["customers", "customers/", "clients", "clients/"]
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json"
    }
    
    for ep in endpoints:
        url = f"{BASE_URL}/{ep}"
        print(f"GET {url}")
        try:
            resp = requests.get(url, headers=headers)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  [SUCCESS] Body len: {len(resp.text)}")
                print(resp.text[:200])
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    debug_customers()
