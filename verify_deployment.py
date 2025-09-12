import requests
import json

print("🚀 Starting production deployment verification...")

url = "https://twshocks-app-79rsx.ondigitalocean.app/api/v1/replay/decision"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiRlJFRV9VU0VSIiwidXNlcl9yb2xlIjoiZnJlZSIsInRpZXIiOiJmcmVlIiwicmVnaXN0ZXJlZF9hdCI6IjIwMjUtMDgtMjBUMTA6MDA6MDBaIn0"
}
payload = {
    "stock_id": "2330",
    "trade_price": 650,
    "trade_date": "2025-09-10"
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=20)

    if response.status_code == 200:
        data = response.json()
        upgrade_prompt = data.get("upgrade_prompt")
        
        print("\n------ API Response Verification ------")
        print(f"✅ Verification successful! Status Code: {response.status_code}")
        print(f"\nType of 'upgrade_prompt': {type(upgrade_prompt)}")
        print("\nContent of 'upgrade_prompt':")
        # Pretty print the JSON object
        print(json.dumps(upgrade_prompt, indent=2, ensure_ascii=False))
        print("------------------------------------\n")

        if isinstance(upgrade_prompt, dict):
            print("🎉 SUCCESS: Deployment is confirmed! The API is returning the new structured format.")
        else:
            print("❌ FAILURE: Deployment is NOT complete. The API is still returning the old string format.")

    else:
        print(f"\n❌ Error: Received status code {response.status_code}")
        print("Response Body:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"\n❌ CRITICAL ERROR: Could not connect to the API.")
    print(f"Error details: {e}")
