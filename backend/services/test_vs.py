import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
try:
    r = requests.get("https://finance.vietstock.vn/hpg", headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("Success! Length:", len(r.text))
        if "HPG" in r.text:
            print("Contains HPG")
except Exception as e:
    print(f"Error: {e}")
