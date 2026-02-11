import requests
import json

def test_tcbs(ticker):
    url = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term?ticker={ticker}&type=stock&resolution=D&countBack=5"
    try:
        r = requests.get(url, timeout=10)
        print(f"TCBS Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][-1]
                print(f"✅ TCBS Data for {ticker}: Close={latest['close']}, Vol={latest['volume']}")
                return True
    except Exception as e:
        print(f"TCBS Error: {e}")
    return False

def test_vndirect(ticker):
    url = f"https://finfo-api.vndirect.com.vn/v4/stock_prices?sort=date&q=code:{ticker}&size=1"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        print(f"VND Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                print(f"✅ VND Data for {ticker}: Close={latest['close']}, Vol={latest['volume']}")
                return True
    except Exception as e:
        print(f"VND Error: {e}")
    return False

if __name__ == "__main__":
    t = "HPG"
    print(f"Testing connectivity for {t}...")
    test_tcbs(t)
    test_vndirect(t)
