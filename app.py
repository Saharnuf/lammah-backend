# app.py
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

# --- الإعدادات ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MOYASAR_SECRET_KEY = os.environ.get("MOYASAR_SECRET_KEY")

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
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        all_records = sheet.get_all_records()

        final_products = []
        for row in all_records:
            name = row.get('المنتج') or "منتج غير معروف"
            try:
                stock = int(row.get('المخزون', 0))
            except:
                stock = 0
            
            # --- استخدام محرك الذكاء (lammah_logic) هنا ---
            # نرسل اسم المنتج كـ url لكي يحاول تصنيفه (شتوي/صيفي)
            analysis = engine.analyze(url=name, stock=stock, city="Riyadh")
            
            final_products.append({
                "name": name,
                "stock": stock,
                # هنا نعرض النتيجة الذكية من ملف المنطق
                "recommendation": f"{analysis['action']}: {analysis['reason']}"
            })
            
        return jsonify({"products": final_products}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# --- مسار ميسر المكتمل ---
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
        # إرجاع رابط الدفع للواجهة
        return jsonify({"payment_url": res_data.get('source', {}).get('transaction_url')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "<h1>مرحباً بك في رادار لماح 🚀</h1><p>السيرفر يعمل ومتصل بميسر وسوبابيس!</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)