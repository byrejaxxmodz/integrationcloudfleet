
import requests
try:
    resp = requests.get("http://127.0.0.1:8000/docs", timeout=20)
    print(f"Server OK: {resp.status_code}")
except Exception as e:
    print(f"Server Error: {e}")
