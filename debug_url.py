import os
import requests
from app.cloudfleet import _headers, BASE_URL

# Test variants
variants = [
    "routes",
    "routes/",
    "route",
    "route/",
    "rutas",
    "rutas/"
]

print(f"Testing API at {BASE_URL} with customerId=1")

for v in variants:
    url = f"{BASE_URL}/{v}?customerId=1"
    try:
        resp = requests.get(url, headers=_headers(), timeout=5)
        print(f"Endpoint '{v}': {resp.status_code}")
        if resp.status_code == 200:
            print(f"SUCCESS: {resp.text[:100]}")
    except Exception as e:
        print(f"Endpoint '{v}': Error {e}")
