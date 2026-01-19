# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from lammah_logic import LammahDecisionEngine

app = Flask(__name__)
CORS(app) # السماح لـ React بالوصول دون قيود

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)