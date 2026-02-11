import requests
print("Start")
try:
    print("Imported requests")
    res = requests.get("https://google.com")
    print(res.status_code)
except Exception as e:
    print(e)
