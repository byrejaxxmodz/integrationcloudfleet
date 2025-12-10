import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.cloudfleet import get_travels

def debug_simple():
    print("=== DEBUG SIMPLE ===")
    
    # query 1
    cnt1 = 0
    try:
        t1 = get_travels(customer_id="1", max_pages=1)
        cnt1 = len(t1 or [])
    except Exception:
        cnt1 = -1
    print(f"COUNT_ID_1: {cnt1}")

    # query 2
    cnt2 = 0
    cnt_match = 0
    try:
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=2)
        created_to = end_dt.isoformat().split('.')[0] + "Z"
        created_from = start_dt.isoformat().split('.')[0] + "Z"
        
        t2 = get_travels(created_from=created_from, created_to=created_to, max_pages=1)
        cnt2 = len(t2 or [])
        
        for t in t2 or []:
             cc = t.get('costCenter')
             cid = t.get('customerId')
             if str(cid) == "1" or (isinstance(cc, dict) and str(cc.get('id')) == "1"):
                 cnt_match += 1
                 
    except Exception:
        cnt2 = -1
        
    print(f"COUNT_DATE: {cnt2}")
    print(f"COUNT_MATCH_PRAXAIR_IN_DATE: {cnt_match}")

if __name__ == "__main__":
    debug_simple()
