import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from lammah_logic import LammahDecisionEngine
from supabase import create_client, Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests 

app = Flask(__name__)
CORS(app) 

# --- الإعدادات وقراءة المفاتيح البيئية ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MOYASAR_SECRET_KEY = os.environ.get("MOYASAR_SECRET_KEY")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDS") # محتوى ملف الـ JSON كاملاً

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
engine = LammahDecisionEngine()

@app.route('/api/leads', methods=['POST'])
def save_lead():
    try:
        data = request.json
        if supabase:
            supabase.table('leads').insert({
                "company": data.get('company'),
                "email": data.get('email')
            }).execute()
            return jsonify({"message": "Lead saved successfully"}), 201
        return jsonify({"error": "Supabase not configured"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-sheet', methods=['POST'])
def analyze_sheet():
    try:
        data = request.json
        sheet_url = data.get('sheet_url')
        
        # --- الجزء المعدل: قراءة مفاتيح قوقل من الذاكرة وليس من ملف ---
        if not GOOGLE_CREDS_JSON:
            return jsonify({"error": "Google Credentials missing in Render settings"}), 500
        
        creds_dict = json.loads(GOOGLE_CREDS_JSON)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # التحقق باستخدام القاموس (Dictionary) مباشرة
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # --------------------------------------------------------

        sheet = client.open_by_url(sheet_url).sheet1
        all_records = sheet.get_all_records()

        final_products = []
        for row in all_records:
            # نحاول قراءة الأعمدة بالعربية كما هي في قوقل شيت
            name = row.get('المنتج') or row.get('اسم المنتج') or "منتج غير معروف"
            try:
                stock = int(row.get('المخزون', 0))
            except:
                stock = 0
            
            # استدعاء محرك الذكاء من ملف lammah_logic
            analysis = engine.analyze(url=name, stock=stock, city="Riyadh")
            
            final_products.append({
                "name": name,
                "stock": stock,
                "recommendation": f"{analysis['action']}: {analysis['reason']}"
            })
            
        return jsonify({"products": final_products}), 200
    except Exception as e:
        # إذا كان الخطأ متعلق بقوقل شيت (مثلاً لم تتم المشاركة)
        return jsonify({"error": f"Connection Error: {str(e)}"}), 500

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    try:
        data = request.json
        user_email = data.get('email')

        payload = {
            "amount": 9900, # 99 ريال
            "currency": "SAR",
            "description": f"اشتراك لماح بريميوم - {user_email}",
            "callback_url": "https://lammah-frontend.vercel.app/dashboard?payment=success",
            "source": { "type": "checkout" }
        }

        response = requests.post(
            "https://api.moyasar.com/v1/payments",
            auth=(MOYASAR_SECRET_KEY, ""),
            json=payload
        )
        
        res_data = response.json()
        return jsonify({"payment_url": res_data.get('source', {}).get('transaction_url')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "<h1>مرحباً بك في رادار لماح 🚀</h1><p>السيرفر يعمل بنظام المفاتيح السحابية ومتصل بميسر!</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)