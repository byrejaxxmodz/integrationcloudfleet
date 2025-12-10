import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.cloudfleet import get_travels

def debug_travels():
    print("=== DEBUG TRAVELS ===")
    
    # 1. Query by Customer ID "1" (Praxair fallback ID)
    print("\n--- Query by CustomerId='1' ---")
    try:
        t1 = get_travels(customer_id="1", max_pages=1)
        print(f"Results: {len(t1)}")
        if t1:
            print(f"First result: {t1[0].get('number')}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Query by Date (last 2 days)
    # CloudFleet requires < 2 months range
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=2)
    
    created_to = end_dt.isoformat().split('.')[0] + "Z"
    created_from = start_dt.isoformat().split('.')[0] + "Z"
    
    print(f"\n--- Query by Date ({created_from} to {created_to}) NO CLIENT FILTER ---")
    try:
        t2 = get_travels(created_from=created_from, created_to=created_to, max_pages=1)
        print(f"Results: {len(t2)}")
        
        # Check for Praxair matches in results
        matches = 0
        for t in t2:
            # Check vehicle cost center or route info
            # We don't have vehicle cost center in travel object directly usually, 
            # but maybe we check 'customerId' or 'costCenter' if present
            cc = t.get('costCenter')
            cid = t.get('customerId')
            if str(cid) == "1" or (isinstance(cc, dict) and str(cc.get('id')) == "1"):
                print(f"  [MATCH] Found Praxair item! ID: {t.get('number')} | CustomerId: {cid} | CostCenter: {cc}")
                matches += 1
                
        print(f"Total matching Praxair: {matches}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_travels()
