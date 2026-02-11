"""
Lightweight VN Stock API Wrapper
Chỉ lấy dữ liệu history, không dùng vnstock (quá nặng cho Vercel)
"""
import requests
from datetime import datetime, timedelta

class VNStockLite:
    """Lightweight alternative to vnstock for Vercel deployment"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        })
    
    def get_historical_data(self, symbol, start_date=None, end_date=None, resolution="1D", data_type="stock"):
        """
        Get historical price data for a symbol using VNDirect TradingView API (Most Stable)
        """
        symbol = symbol.upper()
        
        # Calculate timestamps
        if not start_date:
            start_ts = int((datetime.now() - timedelta(days=90)).timestamp())
        else:
            start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
            
        if not end_date:
            end_ts = int(datetime.now().timestamp())
        else:
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
            
        # === SOURCE: VNDIRECT DCHART API (TradingView format) ===
        try:
            print(f"[VNStockLite] Fetching from VNDirect DChart: {symbol}")
            # resolution: D, 1, 15, 30, 60
            res_map = {"1D": "D", "1m": "1", "15m": "15", "30m": "30", "1H": "60"}
            res = res_map.get(resolution, "D")
            
            url = "https://dchart-api.vndirect.com.vn/dchart/history"
            params = {
                "resolution": res,
                "symbol": symbol,
                "from": start_ts,
                "to": end_ts
            }
            
            # Add random headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://dchart.vndirect.com.vn/'
            }
            
            r = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if data.get('s') == 'ok' and data.get('t'):
                    history = []
                    times = data['t']
                    opens = data['o']
                    highs = data['h']
                    lows = data['l']
                    closes = data['c']
                    volumes = data['v']
                    
                    for i in range(len(times)):
                        try:
                            ts = times[i]
                            d_obj = datetime.fromtimestamp(ts)
                            date_str = d_obj.strftime('%d/%m/%Y')
                            
                            history.append({
                                'date': date_str,
                                'open': float(opens[i]),
                                'high': float(highs[i]),
                                'low': float(lows[i]),
                                'close': float(closes[i]),
                                'volume': float(volumes[i])
                            })
                        except: continue
                        
                    if history:
                        # VNDirect DChart returns chronological order (oldest first)
                        # We usually want newest last for chart plotting which is correct.
                        # But some of my logic might expect newest first?
                        # Actually data_engine expects list of dicts.
                        # The UI chart expects chronological order.
                        # So just return as is.
                        return history
        except Exception as e:
            print(f"[VNStockLite] DChart failed: {e}")
            
        return []
