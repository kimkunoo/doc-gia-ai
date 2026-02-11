import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
import datetime
from datetime import datetime, timedelta
import math

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DataEngine:
    def __init__(self):
        self.session = requests.Session()
        # Premium browser headers to avoid blocks
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://cafef.vn/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        self.session.verify = False

    def get_market_data(self, ticker):
        """
        Main entry point. Returns a rich dictionary with Price, Technicals, and Financials.
        """
        ticker = ticker.upper()
        print(f"[DataEngine] Starting Deep Scan for {ticker}...")
        
        result = {
            "ticker": ticker,
            "source": "CafeF/Analysis",
            "price": 0,
            "volume": 0,
            "change": 0,
            "technicals": {},
            "financials": {},
            "status": "success"
        }

        try:
            # 1. Get Basic Info & Financials (Overview Page)
            cafef_url = self._find_cafef_url(ticker)
            if cafef_url:
                overview_data = self._scrape_overview(cafef_url)
                if overview_data.get('price', 0) > 0:
                    result.update(overview_data)
                result['url'] = cafef_url

            # 2. Get Historical Data & Technical Analysis
            history = self._get_historical_prices(ticker)
            if history:
                # DATA REPAIR: Normalize units if huge discrepancy
                # CafeF might be 97800, History might be 97.8
                if result.get('price', 0) > 0 and len(history) > 0:
                    latest_hist = history[-1]['close']
                    scraped_price = result['price']
                    
                    # Factor detection (approximate)
                    if scraped_price > 1000 and latest_hist < 500: # History is likely in k
                        ratio = scraped_price / latest_hist
                        if 800 < ratio < 1200: # ~1000x difference
                            print(f"[DataEngine] Auto-scaling history x1000 for {ticker}")
                            for h in history:
                                h['open'] = h['open'] * 1000
                                h['high'] = h['high'] * 1000
                                h['low'] = h['low'] * 1000
                                h['close'] = h['close'] * 1000
                    
                    # If history volume is 0, try to patch with previous week average
                    avg_vol = sum(x['volume'] for x in history[-5:]) / 5 if len(history) >= 5 else 0
                    if history[-1]['volume'] == 0:
                         history[-1]['volume'] = avg_vol
                
                result['history'] = history
                # If scraping failed or was 0, trust the history (now normalized)
                if result['price'] == 0:
                    latest = history[-1]
                    result['price'] = latest['close']
                    result['volume'] = latest.get('volume', 0)
                
                tech_signals = self._calculate_technicals(history)
                result['technicals'] = tech_signals

            # 3. Get Raw News
            result['raw_news'] = self._get_ticker_news(ticker)

            # 4. Final Validation
            if result['price'] == 0:
                 # Last ditch effort
                 print(f"[DataEngine] Failure: No real price found for {ticker}")
                 return {"status": "error", "message": f"Không tìm thấy dữ liệu thực tế cho mã {ticker}. Vui lòng kiểm tra lại mã."}
            
            return result

        except Exception as e:
            print(f"[DataEngine] Critical Error: {e}")
            return {"status": "error", "message": "Lỗi truy xuất dữ liệu thị trường."}

    def _find_cafef_url(self, ticker):
        """Find the main profile URL for the ticker on CafeF"""
        # Improved direct guess for speed, fallback to search later if needed
        # Most HOSE/HNX stocks work with this pattern
        return f"https://s.cafef.vn/hose/{ticker}-1.chn"

    def _scrape_overview(self, url):
        """Scrape Price, Volume, EPS, P/E from Overview Page with OG Tag Priority"""
        data = {"price": 0, "volume": 0, "financials": {}, "last_update": ""}
        try:
            r = self.session.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # --- 1. PRIORITY: OG Tags (Pre-rendered and usually live) ---
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                content = og_desc["content"]
                # Pattern: "Giá cổ phiếu ( chiều 06/02/2026): 26,800 VNĐ. Khối lượng 67,073,000"
                # Price Extraction
                p_match = re.search(r'Giá cổ phiếu[^(]*\([^)]*\):\s*([\d\.,]+)', content)
                if p_match:
                    data['price'] = float(p_match.group(1).replace(',', ''))
                
                # Volume Extraction
                v_match = re.search(r'Khối lượng\s*([\d\.,]+)', content)
                if v_match:
                    data['volume'] = int(v_match.group(1).replace(',', ''))

                # Market Cap Extraction
                cap_match = re.search(r'Vốn hóa tt:\s*([\d\.,]+)', content)
                if cap_match:
                    data['financials']['VonHoa'] = cap_match.group(1)

            # --- 2. SECONDARY: BeautifulSoup Selectors (If OG fail or for extra data) ---
            if data['price'] == 0:
                price_el = soup.find(id=re.compile("lblCurrentPrice|lblPrice"))
                if price_el:
                    data['price'] = float(price_el.get_text().replace(',', ''))

            # Financials Table Scraping
            def find_metric(label_patterns):
                for label in soup.find_all(["td", "span", "div"], string=re.compile('|'.join(label_patterns), re.I)):
                    val_el = label.find_next(["td", "span", "div"])
                    if val_el: return val_el.get_text(strip=True)
                return "N/A"

            data['financials'].update({
                "EPS": find_metric(["EPS", "Lợi nhuận mỗi CP"]),
                "PE": find_metric(["P/E", "Hệ số P/E"]),
                "VonHoa": data['financials'].get('VonHoa', find_metric(["Vốn hóa", "Market Cap"]))
            })
            
            return data
        except Exception as e:
            print(f"[DataEngine] Scrape Error for {url}: {e}")
            return data

    def _get_ticker_news(self, ticker):
        """Fetch latest raw news for a specific ticker from CafeF"""
        raw_news = []
        try:
            url = f"https://s.cafef.vn/tin-doanh-nghiep/{ticker}/tin-moi-nhat.chn"
            r = self.session.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for news in the common list structure on CafeF enterprise news page
            # Usually .tlitem or inside specialized lists
            items = soup.select('.tlitem') or soup.select('li.news-item') or soup.find_all('li', class_=re.compile('news-item|doc-item'))
            for item in items[:10]:
                h = item.find(['h3', 'h4', 'a'])
                if h:
                    title = h.get_text(strip=True)
                    date_span = item.find(class_=re.compile('date|time'))
                    date_str = date_span.get_text(strip=True) if date_span else ""
                    raw_news.append(f"{date_str} - {title}")
        except Exception as e:
            print(f"[DataEngine] Ticker News Fetch Error: {e}")
        return raw_news

    def _get_historical_prices(self, ticker):
        """Fetch history with VNStockLite (PRIORITY), fallback to other APIs"""
        ticker = ticker.upper()
        
        # === PRIORITY 1: VNStockLite (Lightweight API wrapper) ===
        try:
            print(f"[DataEngine] Trying VNStockLite API: {ticker}...")
            from services.vnstock_lite import VNStockLite
            vsl = VNStockLite()
            
            # Get 3 months of data
            df = vsl.get_historical_data(
                symbol=ticker, 
                data_type="index" if ticker == "VNINDEX" else "stock"
            )
            
            if df:
                print(f"[OK] VNStockLite SUCCESS: {len(df)} bars for {ticker}")
                return df
        except Exception as e:
            print(f"[DataEngine] VNStockLite failed: {e}")
        
        # === FALLBACK 1: VNINDEX from VNDirect ===
        if ticker == "VNINDEX":
            try:
                print(f"[DataEngine] Fast path for VNINDEX...")
                url = "https://finfo-api.vndirect.com.vn/v4/stock_prices?query=code:VNINDEX&size=100&sort=date:desc"
                r = self.session.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json().get('data', [])
                    if data:
                        history = []
                        for item in data:
                            history.append({
                                "date": datetime.strptime(item['date'], '%Y-%m-%d').strftime('%d/%m/%Y'),
                                "open": float(item.get('adOpen', item.get('adClose', 0))),
                                "high": float(item.get('adHigh', item.get('adClose', 0))),
                                "low": float(item.get('adLow', item.get('adClose', 0))),
                                "close": float(item.get('adClose', 0)),
                                "volume": float(item.get('nmVolume', 0))
                            })
                        history.reverse()
                        return history
            except: pass
        
        # === FALLBACK 2: Yahoo Finance ===
        try:
            import yfinance as yf
            yahoo_ticker = "^VNI" if ticker == "VNINDEX" else f"{ticker}.VN"
            hist = yf.download(yahoo_ticker, period="3mo", interval="1d", progress=False, timeout=2)
            if not hist.empty:
                history = []
                for date, row in hist.iterrows():
                    history.append({
                        "date": date.strftime('%d/%m/%Y'),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": float(row['Volume'])
                    })
                if history: return history
        except: pass
        
        # === FALLBACK 3: SSI API ===
        try:
            print(f"[DataEngine] Trying SSI API: {ticker}...")
            ssi_url = f"https://iboard-query.ssi.com.vn/stock/second/history/{ticker}/1M"
            r = self.session.get(ssi_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data and isinstance(data, dict) and 'data' in data:
                    items = data['data']
                    if items:
                        history = []
                        for item in items[:50]:
                            try:
                                date_str = item.get('tradingDate', '')
                                if date_str:
                                    d_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                    formatted_date = d_obj.strftime('%d/%m/%Y')
                                    
                                    history.append({
                                        "date": formatted_date,
                                        "open": float(item.get('openPrice', item.get('closePrice', 0))),
                                        "high": float(item.get('highestPrice', item.get('closePrice', 0))),
                                        "low": float(item.get('lowestPrice', item.get('closePrice', 0))),
                                        "close": float(item.get('closePrice', 0)),
                                        "volume": float(item.get('totalVolume', 0))
                                    })
                            except:
                                continue
                        
                        if history:
                            history.reverse()
                            return history
        except: pass
        
        # === FINAL FALLBACK: No data ===
        print(f"[WARNING] ALL APIs FAILED for {ticker} history!")
        return []

    

    def _calculate_technicals(self, history):
        """
        Calculates a suite of technical indicators:
        - SMA 20, EMA 20
        - Bollinger Bands (20, 2)
        - RSI (14)
        - MACD (12, 26, 9) - Basic implementation
        - Volume Analysis
        """
        if len(history) < 30: # Need enough data for calculations
            return {"status": "Không đủ dữ liệu (khuyến nghị tối thiểu 30 ngày)"}

        closes = [d['close'] for d in history]
        # volumes = [d.get('volume', 0) for d in history] # CafeF history might not have vol in all rows, let's check
        current_price = closes[-1]
        
        # 1. Moving Averages
        sma20 = sum(closes[-20:]) / 20
        
        # Simple EMA calculation
        def calculate_ema(data, period):
            k = 2 / (period + 1)
            ema = data[0]
            for price in data[1:]:
                ema = (price * k) + (ema * (1 - k))
            return ema

        ema20 = calculate_ema(closes[-40:], 20) # Use a bit more data for EMA stability
        ema50 = calculate_ema(closes[-50:], 50) if len(closes) >= 50 else sma20

        # 2. Bollinger Bands (20, 2)
        variance = sum((x - sma20) ** 2 for x in closes[-20:]) / 20
        std_dev = math.sqrt(variance)
        bb_upper = sma20 + (std_dev * 2)
        bb_lower = sma20 - (std_dev * 2)

        # 3. RSI 14
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        recent_deltas = deltas[-14:]
        gains = [d for d in recent_deltas if d > 0]
        losses = [abs(d) for d in recent_deltas if d < 0]
        
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        
        if avg_loss == 0: rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # 4. MACD (Basic)
        ema12 = calculate_ema(closes[-26-12:], 12)
        ema26 = calculate_ema(closes[-26:], 26)
        macd_line = ema12 - ema26
        # Signal line would be EMA 9 of MACD line, but we need time-series of MACD line for that.
        # For simplicity, we'll just provide MACD line and Trend.

        # 5. Trend & Signals
        trend = "ĐI NGANG"
        if current_price > ema20 and ema20 > ema50: trend = "TĂNG MẠNH"
        elif current_price > ema20: trend = "XU HƯỚNG TĂNG"
        elif current_price < ema20 and ema20 < ema50: trend = "GIẢM MẠNH"
        elif current_price < ema20: trend = "XU HƯỚNG GIẢM"

        # Signal Logic (Simple)
        signal = "CHỜ"
        if rsi < 35 and current_price <= bb_lower: signal = "MUA (HỖ TRỢ/QUÁ BÁN)"
        elif rsi > 65 and current_price >= bb_upper: signal = "BÁN (KHÁNG CỰ/QUÁ MUA)"
        elif trend == "XU HƯỚNG TĂNG" and rsi < 50: signal = "MUA (THEO TREND)"
        
        return {
            "current_price": current_price,
            "sma20": round(sma20, 2),
            "ema20": round(ema20, 2),
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "rsi_14": round(rsi, 2),
            "macd_line": round(macd_line, 2),
            "trend": trend,
            "signal": signal
        }

    def get_market_highlights(self):
        """Fetch VN-Index and hot news using VNStockLite for price stability"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Cache-Control': 'no-cache'
        })

        result = {
            "index": {"code": "VNINDEX", "price": 0, "change": 0, "changePercent": 0, "history": []},
            "news": []
        }
        
        # 1. VNINDEX Fetch via VNStockLite (Stable)
        try:
            print("[DataEngine] Fetching VNINDEX from VNStockLite...")
            from services.vnstock_lite import VNStockLite
            vsl = VNStockLite()
            # Get history (default 90 days)
            history = vsl.get_historical_data("VNINDEX", resolution="1D")
            
            if history and len(history) > 0:
                result['index']['history'] = history
                latest = history[-1]
                
                price = latest['close']
                result['index']['price'] = price
                
                if len(history) >= 2:
                    prev = history[-2]
                    change = price - prev['close']
                    pct = (change / prev['close']) * 100
                    result['index']['change'] = round(change, 2)
                    result['index']['changePercent'] = round(pct, 2)
                    print(f"[DataEngine] VNINDEX Updated: {price} ({change:+.2f})")
                else:
                    print(f"[DataEngine] VNINDEX Updated: {price} (No prev data)")
            else:
                 print("[DataEngine] VNStockLite returned no history for VNINDEX")

        except Exception as e:
            print(f"[DataEngine] VNINDEX Fetch Error: {e}")

        # 2. News Scraping (CafeF)
        try:
            print(f"[DataEngine] Scraping News from CafeF...")
            news_url = "https://cafef.vn/thi-truong-chung-khoan.chn"
            r_news = self.session.get(news_url, timeout=10)
            if r_news.status_code == 200:
                soup = BeautifulSoup(r_news.text, 'html.parser')
                items = soup.select('.tlitem') or soup.select('.tr-item') or soup.select('li.news-item') or soup.select('.itemnews')
                
                for item in items:
                    if len(result['news']) >= 5: break
                    h = item.find(['h3', 'h2', 'a'])
                    if h:
                        title = h.get_text(strip=True)
                        if len(title) < 20: continue
                        a = item.find('a') if item.name != 'a' else item
                        if a and a.get('href'):
                            link = a['href']
                            if link.startswith('/'): link = "https://cafef.vn" + link
                            if not any(n['title'] == title for n in result['news']):
                                result['news'].append({"title": title, "url": link})
        except Exception as e:
            print(f"[DataEngine] CafeF Scraping failed: {e}")

        # 3. Fallback News
        if not result['news']:
             result['news'] = [
                {"title": "Thị trường: Nhà đầu tư chờ đợi tín hiệu từ KQKD quý mới", "url": "https://cafef.vn"},
                {"title": "Dòng tiền khối ngoại đang có xu hướng quay trở lại", "url": "https://cafef.vn"},
                {"title": "Góc nhìn kỹ thuật: VN-Index đang tích lũy tại vùng hỗ trợ", "url": "https://cafef.vn"}
            ]
        
        result['news'] = result['news'][:5]
        return result

    def _fallback_mock(self, ticker):
        return {
            "source": "Mock (System Failure)",
            "ticker": ticker,
            "price": 25000,
            "technicals": {"rsi_14": 55, "trend": "Unknown"},
            "financials": {"EPS": "2.5", "PE": "10.0"}
        }
