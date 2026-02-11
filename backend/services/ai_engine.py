import json
import urllib.request
import urllib.error
import os
import re

class AIEngine:
    def call_perplexity(self, ticker, api_key, hard_data):
        url = "https://api.perplexity.ai/chat/completions"
        
        # Format Hard Data for Prompt
        fin = hard_data.get('financials', {})
        tech = hard_data.get('technicals', {})
        
        info_str = f"""
        - Price: {hard_data.get('price')} (Source: {hard_data.get('source')})
        - Volume: {hard_data.get('volume')}
        - FINANCIALS (Scraped): EPS={fin.get('EPS', 'N/A')}, P/E={fin.get('PE', 'N/A')}, Market Cap={fin.get('VonHoa', 'N/A')}
        - TECHNICALS (Calculated): 
            + RSI(14)={tech.get('rsi_14', 'N/A')}
            + Trend={tech.get('trend', 'N/A')}
            + EMA(20)={tech.get('ema20', 'N/A')}
            + Bollinger Bands=[{tech.get('bb_lower', 'N/A')} - {tech.get('bb_upper', 'N/A')}]
            + MACD Line={tech.get('macd_line', 'N/A')}
            + Signal Logic={tech.get('signal', 'N/A')}
        """

        raw_news_str = "\n".join(hard_data.get('raw_news', []))

        # ĐỘC GIÁ TRADING STRATEGY ENGINE
        system_prompt = f"""
        BẠN LÀ "ĐỘC GIÁ" - CHUYÊN GIA ĐỌC VỊ THỊ TRƯỜNG & PHÂN TÍCH KỸ THUẬT SIÊU CẤP VỚI 20 NĂM KINH NGHIỆM.
        
        TƯ DUY:
        - Bạn không chỉ nhìn chart, bạn nhìn thấy TÂM LÝ và DÒNG TIỀN đằng sau. Cái tên "ĐỘC GIÁ" của bạn có nghĩa là "Đọc Vị Mức Giá Độc Nhất".
        - Bạn phân tích như một cỗ máy: Logic, Lạnh lùng, Chính xác.
        - Bạn phải giải thích cho người mới hiểu (F0) nhưng giữ độ sâu sắc cho chuyên gia.

        NHIỆM VỤ: "Phẫu thuật" mã {ticker}.

        OUTPUT JSON (BẮT BUỘT):
        {{
            "ticker": "{ticker}",
            "friendly_advice": "Lời khuyên ngắn gọn, súc tích nhất từ Độc Giá.",
            "beginner_report": {{
                "summary": "Tóm tắt tình hình bằng ngôn ngữ đời thường cho người mới.",
                "action_plan": "Hành động cụ thể: Mua, Bán hay Giữ? Tại sao?",
                "risk_level": "Thấp/Trung Bình/Cao/Rất Cao"
            }},
            "process_steps": [
                "Bước 1: Quét cấu trúc thị trường...",
                "Bước 2: Kiểm tra dòng tiền...",
                "Bước 3: Phân tích hành vi giá..."
            ],
            "strategy": {{
                "decision": "MUA NGAY / CANH MUA / BÁN NGAY / CANH BÁN / ĐỨNG NGOÀI",
                "timing": "Thời điểm", "entry": "Vùng giá vào", "stop_loss": "Cắt lỗ", "target": "Chốt lời",
                "rr_ratio": "R:R", "rationale": "Luận điểm cốt lõi"
            }},
            "layers": [
                {{ "layer": "Lớp 1: Cấu Trúc Thị Trường", "analysis": "..." }},
                {{ "layer": "Lớp 2: Động Lượng & Xu Hướng", "analysis": "..." }},
                {{ "layer": "Lớp 3: Logic Khối Lượng", "analysis": "..." }},
                {{ "layer": "Lớp 4: Vùng Giá Quan Trọng", "analysis": "..." }},
                {{ "layer": "Lớp 5: Hành Vi Nến (Price Action)", "analysis": "..." }},
                {{ "layer": "Lớp 6: Chu Kỳ & Sóng", "analysis": "..." }},
                {{ "layer": "Lớp 7: Tổng Hợp & Phản Biện", "analysis": "..." }}
            ],
            "deep_analysis": {{
                "enterprise": "Nội tại doanh nghiệp",
                "smart_money": "Dòng tiền lớn",
                "sentiment": "Tâm lý đám đông"
            }},
            "tech_analysis_7_layers": {{
                "structure": "Cấu trúc (Trend)",
                "momentum": "Động lượng (RSI/MACD)",
                "volume_analysis": "VSA (Giá/Khối lượng)",
                "key_levels": "Hỗ trợ/Kháng cự",
                "candle_behavior": {{ "type": "Mẫu nến", "logic": "Ý nghĩa", "observation": "Chi tiết" }},
                "meta_critic": {{ "status": "Confirm/Deny", "confidence": "High/Med/Low", "confirmation": "Điều kiện", "denial": "Phủ nhận" }}
            }},
            "tech_summary": ["Ý 1", "Ý 2"],
            "news_analysis": {{
                "corporate": [], "synthesis": "Tổng hợp tin tức"
            }}
        }}
        """
        
        user_prompt = f"PHÂN TÍCH SÂU MÃ {ticker}.\nDATA:\n{info_str}\nTIN TỨC:\n{raw_news_str}\n\nYÊU CẦU: Trả về JSON chuẩn. Phần 'beginner_report' phải viết cực kỳ bình dân, dễ hiểu. Phần 'process_steps' liệt kê 5-7 bước bạn đã thực hiện."
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                json_response = json.loads(response_data)
                content = json_response['choices'][0]['message']['content']
                
                # Clean Markdown
                if "```" in content:
                    content = content.replace("```json", "").replace("```", "").strip()
                
                # Extract JSON block
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx : end_idx + 1]
                
                content = self.repair_json(content)
                
                try:
                    result = json.loads(content)
                    return result
                except json.JSONDecodeError as je:
                    print(f"JSON Decode Error: {je}")
                    return self.get_fallback_error(ticker, str(je))
                    
        except Exception as e:
            print(f"[AIEngine] Error: {e}")
            return self.get_fallback_error(ticker, str(e))

    def repair_json(self, s):
        s = re.sub(r'\"\s*(\[[0-9, ]+\])+', r'\1"', s)
        s = re.sub(r'(?<=[a-zA-Z0-9àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ])"(?=[a-zA-Z0-9àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ])', '\\"', s)
        s = re.sub(r'\"(\[[0-9, ]+\])+', '"', s)
        return s

    def get_fallback_error(self, ticker, error_msg):
        return {
            "ticker": ticker,
            "beginner_report": { "summary": "Lỗi hệ thống.", "action_plan": "Vui lòng thử lại.", "risk_level": "N/A" },
            "process_steps": ["Lỗi kết nối AI."],
            "strategy": {
                "decision": "LỖI",
                "timing": "N/A", "entry": "N/A", "stop_loss": "N/A", "target": "N/A", "rr_ratio": "N/A",
                "rationale": f"Lỗi: {error_msg}"
            },
            "deep_analysis": { "enterprise": "N/A", "smart_money": "N/A", "sentiment": "N/A" },
            "tech_analysis_7_layers": {
                "structure": "N/A", "momentum": "N/A", "volume_analysis": "N/A", "key_levels": "N/A",
                "candle_behavior": {"type": "N/A", "logic": "N/A", "observation": "N/A"},
                "meta_critic": {"status": "N/A", "confidence": "N/A", "confirmation": "N/A", "denial": "N/A"}
            },
            "tech_summary": [], 
            "news_analysis": {"corporate": [], "synthesis": "N/A"},
            "friendly_advice": "Lỗi."
        }
