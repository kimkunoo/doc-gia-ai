import http.server
import socketserver
import webbrowser
import os
import json
import sys

# Ensure we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_engine import DataEngine
from services.ai_engine import AIEngine

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend')

# Initialize Engines
data_engine = DataEngine()
ai_engine = AIEngine()

class NukidaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve frontend files by default
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/analyze':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                ticker = request_data.get('ticker')
                api_key = request_data.get('apiKey') or os.environ.get('PPLX_API_KEY')
                
                if not ticker:
                    self._send_response(400, {"error": "Thiếu mã cổ phiếu"})
                    return
                
                if not api_key:
                    # FALLBACK: Use provided API Key if not present
                    api_key = "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"

                # Normalize Ticker
                ticker = filter(str.isalnum, ticker)
                ticker = "".join(ticker).upper()

                # Step 1: Get Hard Data (Price, VNStock, News)
                print(f"[Nukida] Fetching Data for {ticker}...")
                hard_data = data_engine.get_market_data(ticker)
                
                # Step 2: AI Analysis (Nukida Strategy)
                print(f"[Nukida] Ultra-Deep Analysis with AI...")
                ai_result = ai_engine.call_perplexity(ticker, api_key, hard_data)
                
                # Step 3: DATA MERGE (Fix N/A Issue)
                # We must attach the raw metrics so the Frontend can display them in the Fast Metrics grid
                ai_result['financials'] = hard_data.get('financials', {})
                ai_result['technicals'] = hard_data.get('technicals', {})
                ai_result['chart_data'] = hard_data.get('history', [])
                ai_result['current_price'] = hard_data.get('price')
                ai_result['percent_change'] = hard_data.get('percent_change', '0%')

                # SAFE SERIALIZATION
                # Ensure no NaN or Inf which breaks JSON.parse in frontend
                def safe_serialize(obj):
                    if isinstance(obj, float):
                        if obj != obj: return None # NaN
                        if obj == float('inf') or obj == float('-inf'): return None
                    elif isinstance(obj, dict):
                        return {k: safe_serialize(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [safe_serialize(x) for x in obj]
                    return obj

                response_data = safe_serialize(ai_result)
                self._send_response(200, response_data)

            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_response(500, {"error": str(e)})
        else:
            self.send_error(404)

    def _send_response(self, code, data):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

def start_server():
    # Change to backend dir to ensure imports work if run from there
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.ThreadingTCPServer(("", PORT), NukidaHandler) as httpd:
        print(f"NUKIDA TRADING APP RUNNING: http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
            print("Server stopped.")

if __name__ == "__main__":
    start_server()
