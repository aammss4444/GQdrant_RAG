
import requests
import json

url = "http://localhost:8000/api/chat"
payload = {"message": "What is AI?"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    response_json = response.json()
    print("Response Content:")
    print(response_json.get("response", "No response field found"))
except Exception as e:
    print(f"Error: {e}")
