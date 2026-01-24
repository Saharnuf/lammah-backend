# lammah_logic.py
import random

class LammahDecisionEngine:
    def __init__(self):
        # قاعدة بيانات الطقس الافتراضية للمدن السعودية (تحدث لحظياً في الأنظمة المتقدمة)
        self.weather_db = {
            "Riyadh": {"temp": 14, "season": "winter"},
            "Jeddah": {"temp": 29, "season": "summer"},
            "Dammam": {"temp": 17, "season": "winter"}
        }

    def classify_product(self, url):
        """تحليل محتوى الرابط لتحديد نوع المنتج"""
        url_lower = url.lower()
        if any(word in url_lower for word in ['hoodie', 'jacket', 'wool', 'جاكيت', 'هودي', 'شتوي']):
            return "winter_wear"
        if any(word in url_lower for word in ['bermuda', 'shorts', 'swim', 'برمودا', 'شورت', 'صيفي']):
            return "summer_wear"
        return "neutral"

    def analyze(self, url, stock, city, daily_sales=None):
        # 1. المرحلة الأولى: تصنيف المنتج
        product_type = self.classify_product(url)
        product_name = url.split('/')[-1].replace('-', ' ').title() or "Product"
        
        # 2. محرك التنبؤ (Prediction Engine)
        # محاكاة معدل البيع إذا لم يتوفر ربط حقيقي بعد
        avg_daily_sales = daily_sales if daily_sales else random.randint(2, 10)
        days_until_out_of_stock = round(stock / avg_daily_sales) if avg_daily_sales > 0 else 999
        
        # نظام الإشارات (🔴🟡🟢)
        status_color = "🟢" if days_until_out_of_stock > 7 else "🟡" if days_until_out_of_stock > 3 else "🔴"
        
        # اقتراح كمية إعادة الطلب لتغطية 30 يوم
        reorder_quantity = max(0, (avg_daily_sales * 30) - stock)

        city_data = self.weather_db.get(city, {"temp": 25, "season": "neutral"})
        score = 70 

        if stock <= 0:
            return {
                "product": product_name, "action": "Zero Budget 🛑",
                "reason": "نفد المخزون! أوقف الإعلانات فوراً لتجنب الهدر.", "score": 0,
                "prediction": {"days": 0, "status": "🔴", "reorder": reorder_quantity}
            }

        prediction_msg = f" | المتوقع نفاده خلال {days_until_out_of_stock} أيام {status_color}"
        
        final_score = min(max(score, 0), 100)
        action = "Scale Up 🚀" if final_score > 80 else "Maintain ✅" if final_score > 50 else "Reduce ⚠️"

        return {
            "product": product_name,
            "action": action,
            "reason": f"المخزون {stock} قطعة. {prediction_msg}",
            "score": final_score,
            "prediction": {
                "days": days_until_out_of_stock,
                "status": status_color,
                "reorder": reorder_quantity,
                "daily_avg": avg_daily_sales
            }
        }