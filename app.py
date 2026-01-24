# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from lammah_logic import LammahDecisionEngine

app = Flask(__name__)
CORS(app) # السماح لـ React بالوصول دون قيود

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- هنا تعريف الدالة التي كانت مفقودة ---
def test_lammah_connection(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # تأكدي أن اسم ملف الـ json هنا يطابق اسم ملفك بالضبط
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        all_data = sheet.get_all_records()
        print("🚀 تم الاتصال بنجاح! البيانات هي:")
        print(all_data)
        return all_data
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الاتصال: {e}")
        return None

engine = LammahDecisionEngine()
LEADS_PATH = 'leads.json'

@app.route('/api/leads', methods=['POST'])
def save_lead():
    try:
        data = request.json
        leads = []
        if os.path.exists(LEADS_PATH):
            with open(LEADS_PATH, 'r', encoding='utf-8') as f:
                leads = json.load(f)
        
        leads.append(data)
        with open(LEADS_PATH, 'w', encoding='utf-8') as f:
            json.dump(leads, f, ensure_ascii=False, indent=4)
        
        return jsonify({"message": "Lead saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_product():
    try:
        data = request.json
        # استلام البيانات: URL, Stock, City
        result = engine.analyze(
            url=data.get('url', ''),
            stock=int(data.get('stock', 0)),
            city=data.get('city', 'Riyadh')
        )
        
        # محاكاة الربط البنكي والقنوات
        result['sync'] = {
            "bank": "Connected (Encrypted)",
            "channels": data.get('channels', ['Snapchat'])
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

       # تأكدي أن كلمة @ تكون في بداية السطر بدون أي فراغ قبلها
@app.route('/')
def home():
    return "<h1>مرحباً بك في رادار لماح 🚀</h1><p>السيرفر يعمل بنجاح والاتصال بقوقل شيت جاهز!</p>"

# سطر if يجب أن يكون في بداية السطر تماماً
if __name__ == '__main__':
    my_sheet_link = "hhttps://docs.google.com/spreadsheets/d/14QXfUm_a8vwGLYGdULAGOh1rfaEnoRZmrboJTR3FRQk/edit?gid=0#gid=0"
    
    # تأكدي أن هذه الأسطر تحت if مزاحة للداخل بـ 4 مسافات (Tab)
    test_lammah_connection(my_sheet_link)
    app.run(host='127.0.0.1', port=5000, debug=True)