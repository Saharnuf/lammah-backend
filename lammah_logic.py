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

    def analyze(self, url, stock, city):
        # 1. المرحلة الأولى: فلتر المخزون (Inventory Priority)
        product_type = self.classify_product(url)
        product_name = url.split('/')[-1].replace('-', ' ').title() or "Product"

        # تحديد عتبة المخزون المنخفض سياقياً
        low_stock_limit = 15 if product_type != "neutral" else 5

        if stock <= 0:
            return {
                "product": product_name, "action": "Zero Budget 🛑",
                "reason": "Stock is empty. Advertising stopped to save budget.", "score": 0
            }
        
        if stock < low_stock_limit:
            return {
                "product": product_name, "action": "Reduce Budget ⚠️",
                "reason": f"Low stock ({stock} units). Scaling down to avoid overselling.", "score": 30
            }

        # 2. المرحلة الثانية: منطق الطقس (Weather Logic)
        city_data = self.weather_db.get(city, {"temp": 25, "season": "neutral"})
        score = 70 # درجة أساسية
        weather_comment = "Weather is compatible."

        if city_data["season"] == "winter" and product_type == "summer_wear":
            score -= 40
            weather_comment = f"Product is summer-wear, but {city} is cold ({city_data['temp']}°C)."
        elif city_data["season"] == "winter" and product_type == "winter_wear":
            score += 20
            weather_comment = f"Perfect match! High demand for winter gear in {city}."

        # 3. المرحلة الثالثة: المحاكاة للترند (Saudi Trends)
        trends = ["Winter Camping", "Riyadh Season", "Founding Day", "Modest Fashion"]
        current_trend = random.choice(trends)
        if "Winter" in current_trend and product_type == "winter_wear":
            score += 10
            weather_comment += f" | Trending: {current_trend} on TikTok KSA."

        # القرار النهائي
        final_score = min(max(score, 0), 100)
        action = "Scale Up 🚀" if final_score > 80 else "Maintain ✅" if final_score > 50 else "Reduce ⚠️"

        return {
            "product": product_name,
            "action": action,
            "reason": weather_comment,
            "score": final_score
        }