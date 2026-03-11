"""Quick diagnostic script to test Azure Video Indexer credentials."""
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import requests
from azure.identity import DefaultAzureCredential

print("--- Testing Azure Credentials ---")
tenant = os.getenv("AZURE_TENANT_ID", "NOT SET")
client = os.getenv("AZURE_CLIENT_ID", "NOT SET")
secret = os.getenv("AZURE_CLIENT_SECRET", "")
print(f"TENANT_ID: {tenant[:8]}...")
print(f"CLIENT_ID: {client[:8]}...")
print(f"CLIENT_SECRET set: {bool(secret)}, length: {len(secret)}")

# Step 1: Get ARM token
print("\n--- Step 1: ARM Token ---")
try:
    cred = DefaultAzureCredential()
    token = cred.get_token("https://management.azure.com/.default")
    arm_token = token.token
    print(f"ARM Token OK (length={len(arm_token)})")
except Exception as e:
    print(f"ARM Token FAILED: {e}")
    exit(1)

# Step 2: Get VI Account Token
print("\n--- Step 2: VI Account Token ---")
sub = os.getenv("AZURE_SUBSCRIPTION_ID")
rg = os.getenv("AZURE_RESOURCE_GROUP")
vi_name = os.getenv("AZURE_VI_NAME", "myproject001")

url = (
    f"https://management.azure.com/subscriptions/{sub}"
    f"/resourceGroups/{rg}"
    f"/providers/Microsoft.VideoIndexer/accounts/{vi_name}"
    f"/generateAccessToken?api-version=2024-01-01"
)
headers = {"Authorization": f"Bearer {arm_token}"}
payload = {"permissionType": "Contributor", "scope": "Account"}

resp = requests.post(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"ERROR: {resp.text}")
else:
    print("VI Account Token obtained successfully!")
