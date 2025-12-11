import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# Original from .env
ENV_URL = os.getenv("CLOUDFLEET_API_URL", "https://fleet.cloudfleet.com/api/v1").rstrip("/")
TOKEN = os.getenv("CLOUDFLEET_API_TOKEN", "")

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def probe():
    print(f"Loaded Token: {TOKEN[:5]}...{TOKEN[-5:] if TOKEN else ''}")
    
    base_urls = [
        ENV_URL,
        ENV_URL.replace("/api/v1", "/api"),
        ENV_URL.replace("/api/v1", ""),
        "https://fleet.cloudfleet.com/api/v2" 
    ]
    
    # Clean duplicates
    base_urls = list(set(base_urls))
    
    print(f"Probing Base URLs: {base_urls}")

    valid_base = None
    customer_id = None

    # 1. Find valid base URL and get a customer
    for base in base_urls:
        print(f"\n--- Testing Base: {base} ---")
        try:
            url = f"{base}/customers"
            print(f"GET {url}")
            res = requests.get(url, headers=get_headers(), timeout=10)
            print(f"Status: {res.status_code}")
            
            if res.ok:
                print("SUCCESS: Found customers endpoint.")
                valid_base = base
                data = res.json()
                items = data if isinstance(data, list) else data.get("items", [])
                if items:
                    c = items[0]
                    customer_id = c.get("id")
                    print(f"Sample Customer ID: {customer_id}")
                break
            else:
                 print(f"Fail: {res.text[:100]}")

        except Exception as e:
            print(f"Exception: {e}")

    if not valid_base:
        print("\nCRITICAL: Could not find valid customers endpoint on any base URL.")
        return

    if not customer_id:
        print("\nCRITICAL: Customers endpoint worked but returned no items.")
        return

    # 2. Probe Locations with valid base and customer_id
    print(f"\n--- Probing Locations using Base: {valid_base} and Customer: {customer_id} ---")
    
    endpoints = [
        "locations",
        f"locations?customerId={quote(str(customer_id))}",
        f"customers/{quote(str(customer_id))}/locations",
        "places",
        f"places?customerId={quote(str(customer_id))}",
        "sites",
        "nodes"
    ]

    for ep in endpoints:
        url = f"{valid_base}/{ep}"
        print(f"\nTrying: {ep}")
        try:
            res = requests.get(url, headers=get_headers(), timeout=10)
            print(f"Status: {res.status_code}")
            if res.ok:
                print("SUCCESS! Response snippet:", str(res.json())[:150])
            elif res.status_code == 404:
                 print("404 Not Found")
            else:
                 print(f"Error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"Ex: {e}")

if __name__ == "__main__":
    probe()
