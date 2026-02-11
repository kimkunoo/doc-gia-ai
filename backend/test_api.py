import requests
import json
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

API_KEY = "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"
URL = "https://api.perplexity.ai/chat/completions"

payload = {
    "model": "sonar-pro",
    "messages": [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Hello, are you working?"}
    ]
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print(f"Testing Perplexity API with Key: {API_KEY[:5]}...{API_KEY[-5:]}")
print(f"Model: {payload['model']}")

try:
    response = requests.post(URL, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response JSON keys:")
        data = response.json()
        print(list(data.keys()))
        print("Content sample: " + str(data)[:100])
    
    else:
        print("Error Response:")
        print(response.content)
except Exception as e:
    print(f"FAILED: {e}")
    if 'response' in locals():
         print(response.content)
