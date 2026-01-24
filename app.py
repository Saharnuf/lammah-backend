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
# تفعيل CORS بشكل كامل للسماح للفرونت اند بالاتصال من أي مكان (Vercel)
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

# --- الإعدادات وقراءة المفاتيح البيئية ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MOYASAR_SECRET_KEY = os.environ.get("MOYASAR_SECRET_KEY")

# محرك التنبؤ والذكاء
engine = LammahDecisionEngine()

# إعداد اتصال Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

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
        return jsonify({"error": "Supabase connection not established"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-sheet', methods=['POST'])
def analyze_sheet():
    try:
        data = request.json
        sheet_url = data.get('sheet_url')
        
        # 1. جلب مفاتيح قوقل من إعدادات Render (Environment Variables)
        google_creds_json = os.environ.get("GOOGLE_CREDS")
        
        if not google_creds_json:
            return jsonify({"error": "GOOGLE_CREDS missing in server settings"}), 500
        
        # 2. تحويل النص إلى قاموس (Dictionary) والدخول للنظام
        creds_dict = json.loads(google_creds_json)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # الربط باستخدام القاموس مباشرة (حل مشكلة No such file)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # 3. فتح الجدول وقراءة البيانات
        sheet = client.open_by_url(sheet_url).sheet1
        all_records = sheet.get_all_records()

        final_products = []
        for row in all_records:
            # دعم أسماء الأعمدة بالعربية
            name = row.get('المنتج') or row.get('اسم المنتج') or "منتج غير معروف"
            try:
                stock_val = row.get('المخزون') or row.get('الكمية') or 0
                stock = int(stock_val)
            except:
                stock = 0
            
            # استدعاء محرك الذكاء (lammah_logic)
            analysis = engine.analyze(url=name, stock=stock, city="Riyadh")
            
            final_products.append({
                "name": name,
                "stock": stock,
                "recommendation": f"{analysis['action']}: {analysis['reason']}"
            })
            
        return jsonify({"products": final_products}), 200

    except gspread.exceptions.PermissionDenied:
        return jsonify({"error": "Permission Denied: فضلاً شارك الملف مع إيميل الخدمة الظاهر في الموقع"}), 403
    except Exception as e:
        return jsonify({"error": f"Connection Error: {str(e)}"}), 500

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    try:
        data = request.json
        user_email = data.get('email')

        # استخدام مفاتيح Moyasar للبيئة التجريبية أو الحقيقية حسب الإعدادات
        payload = {
            "amount": 9900,  # 99.00 SAR
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
        
        if response.status_code != 201:
            return jsonify({"error": res_data.get('message', 'Payment creation failed')}), response.status_code

        return jsonify({"payment_url": res_data.get('source', {}).get('transaction_url')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return """
    <div style="text-align:center; padding:50px; font-family: sans-serif;">
        <h1>رادار لماح 🚀 يعمل بنجاح</h1>
        <p>السيرفر متصل بقاعدة البيانات وبوابة الدفع ومحرك الذكاء.</p>
        <div style="color: green;">● Cloud System Active</div>
    </div>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)