from app.quota_rules import get_quota_for_date, QUOTA_MATRIX

print("Testing Quota Rules directly...")

# Test Exact Match
client = "CCM PRAXAIR"
sede = "YUMBO"
date = "2025-12-12" # Friday
print(f"Testing ('{client}', '{sede}', '{date}')")
q = get_quota_for_date(client, sede, date)
print(f"Result: {q}")

# Test with trailing spaces match
client = "CCM PRAXAIR "
print(f"Testing ('{client}', '{sede}', '{date}')")
q = get_quota_for_date(client, sede, date)
print(f"Result: {q}")

# Test Case Sensitivity
client = "Ccm Praxair"
print(f"Testing ('{client}', '{sede}', '{date}')")
q = get_quota_for_date(client, sede, date)
print(f"Result: {q}")

# Test Partial Match (if explicit fails)
client = "PRAXAIR"
print(f"Testing ('{client}', '{sede}', '{date}')")
q = get_quota_for_date(client, sede, date)
print(f"Result: {q}")

# Verify Keys in Matrix
print("\nVerifying Keys in QUOTA_MATRIX:")
for k in QUOTA_MATRIX.keys():
    if "PRAXAIR" in k[0]:
        print(k)
