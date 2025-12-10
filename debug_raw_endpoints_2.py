import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CLOUDFLEET_API_URL").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")

def debug_endpoints():
    endpoints = ["routes", "travels"]
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    for ep in endpoints:
        url = f"{BASE_URL}/{ep}"
        print(f"GET {url}")
        try:
            resp = requests.get(url, headers=headers)
            print(f"  Status: {resp.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    debug_endpoints()
