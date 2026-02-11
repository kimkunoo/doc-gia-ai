from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json

# Ensure we can import services
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from backend.services.data_engine import DataEngine
from backend.services.ai_engine import AIEngine

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Initialize Engines
data_engine = DataEngine()
ai_engine = AIEngine()

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        ticker = data.get('ticker')
        api_key = data.get('apiKey') or os.environ.get('PPLX_API_KEY')
        
        if not ticker:
            return jsonify({"error": "Thiếu mã cổ phiếu"}), 400
            
        if not api_key:
            return jsonify({"error": "Thiếu API Key. Vui lòng cấu hình trên Vercel Settings -> Environment Variables."}), 400

        # Normalize Ticker
        ticker = "".join(filter(str.isalnum, ticker)).upper()

        # Step 1: Get Hard Data
        hard_data = data_engine.get_market_data(ticker)
        
        # Step 2: AI Analysis
        ai_result = ai_engine.call_perplexity(ticker, api_key, hard_data)
        
        # Step 3: DATA MERGE
        ai_result['financials'] = hard_data.get('financials', {})
        ai_result['technicals'] = hard_data.get('technicals', {})
        ai_result['chart_data'] = hard_data.get('history', [])
        ai_result['current_price'] = hard_data.get('price')
        ai_result['percent_change'] = hard_data.get('percent_change', '0%')

        return jsonify(ai_result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
