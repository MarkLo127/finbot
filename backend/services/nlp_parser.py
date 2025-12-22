"""
NLP 解析器
解析中文記帳指令，提取金額、類別、日期等資訊
"""

import re
import jieba
from datetime import date
from typing import Optional, Dict, Any, List

from utils.date_parser import DateParser


class NLPParser:
    """中文記帳指令解析器"""
    
    # 類別關鍵字映射
    CATEGORY_KEYWORDS = {
        "餐飲": ["吃", "餐", "飯", "午餐", "晚餐", "早餐", "宵夜", "飲料", "咖啡", "奶茶", 
                "便當", "麵", "火鍋", "燒烤", "外食", "食", "喝", "零食", "點心", "蛋糕"],
        "交通": ["車", "捷運", "公車", "uber", "計程車", "高鐵", "火車", "機票", "加油", 
                "停車", "通勤", "騎", "搭", "坐車", "交通"],
        "娛樂": ["電影", "遊戲", "KTV", "唱歌", "玩", "門票", "旅遊", "遊", "看展", 
                "演唱會", "娛樂", "訂閱", "Netflix", "Spotify"],
        "購物": ["買", "購", "衣服", "鞋", "包", "3C", "電器", "手機", "電腦", 
                "網購", "蝦皮", "淘寶", "百貨", "超市", "便利商店", "全聯"],
        "醫療": ["醫", "藥", "看診", "掛號", "健檢", "牙", "眼科", "診所", "醫院"],
        "居住": ["房租", "水電", "電費", "水費", "瓦斯", "管理費", "網路", "cable", 
                "租金", "房貸", "維修"],
        "教育": ["書", "課", "學費", "補習", "教材", "文具", "考試", "證照", "線上課程"],
        "薪資": ["薪", "薪水", "工資", "發薪", "月薪", "獎金", "年終"],
        "投資": ["股", "基金", "利息", "股利", "配息", "投資收益"],
        "其他收入": ["收入", "入帳", "轉帳收入", "紅包", "禮金", "中獎"],
    }
    
    # 收入類別
    INCOME_CATEGORIES = {"薪資", "投資", "其他收入"}
    
    # 金額數字中文對照
    CHINESE_NUMS = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '萬': 10000,
        '兩': 2, '两': 2
    }
    
    @classmethod
    def parse(cls, text: str) -> Dict[str, Any]:
        """
        解析記帳指令
        
        回傳格式：
        {
            "amount": float,           # 金額
            "type": str,               # "income" 或 "expense"
            "category": str,           # 類別名稱
            "date": date,              # 日期
            "description": str,        # 描述
            "confidence": float,       # 解析信心度 0-1
            "raw_text": str           # 原始文字
        }
        """
        result = {
            "amount": None,
            "type": "expense",
            "category": None,
            "date": date.today(),
            "description": text.strip(),
            "confidence": 0.0,
            "raw_text": text
        }
        
        # 1. 解析金額
        amount = cls._extract_amount(text)
        if amount:
            result["amount"] = amount
            result["confidence"] += 0.4
        
        # 2. 解析日期
        parsed_date = DateParser.parse(text)
        if parsed_date:
            result["date"] = parsed_date
            result["confidence"] += 0.1
        
        # 3. 解析類別
        category = cls._extract_category(text)
        if category:
            result["category"] = category
            result["type"] = "income" if category in cls.INCOME_CATEGORIES else "expense"
            result["confidence"] += 0.4
        else:
            # 預設類別
            result["category"] = "其他收入" if "收入" in text else "其他"
            result["confidence"] += 0.1
        
        # 4. 清理描述
        result["description"] = cls._clean_description(text)
        
        return result
    
    @classmethod
    def parse_query(cls, text: str) -> Dict[str, Any]:
        """
        解析查詢指令
        
        回傳格式：
        {
            "query_type": str,         # "summary", "trend", "category", "compare"
            "category": str,           # 查詢的類別（可選）
            "period": str,             # "day", "week", "month", "year"
            "start_date": date,        # 起始日期
            "end_date": date,          # 結束日期
            "chart_type": str         # "pie", "line", "bar"（可選）
        }
        """
        today = date.today()
        result = {
            "query_type": "summary",
            "category": None,
            "period": "month",
            "start_date": today.replace(day=1),
            "end_date": today,
            "chart_type": None
        }
        
        # 解析時間範圍
        if "今天" in text or "今日" in text:
            result["period"] = "day"
            result["start_date"] = today
        elif "這週" in text or "本週" in text:
            result["period"] = "week"
            result["start_date"] = today - timedelta(days=today.weekday())
        elif "上個月" in text or "上月" in text:
            result["period"] = "month"
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            result["start_date"] = last_month_end.replace(day=1)
            result["end_date"] = last_month_end
        elif "這個月" in text or "本月" in text:
            result["period"] = "month"
            result["start_date"] = today.replace(day=1)
        elif "今年" in text:
            result["period"] = "year"
            result["start_date"] = today.replace(month=1, day=1)
        
        # 解析 N 個月
        match = re.search(r'近?(\d+|[一二三四五六七八九十]+)\s*個?月', text)
        if match:
            from datetime import timedelta
            months = cls._parse_chinese_number(match.group(1))
            result["start_date"] = today.replace(day=1)
            for _ in range(months - 1):
                result["start_date"] = (result["start_date"] - timedelta(days=1)).replace(day=1)
        
        # 解析類別
        for category in cls.CATEGORY_KEYWORDS.keys():
            if category in text:
                result["category"] = category
                result["query_type"] = "category"
                break
        
        # 解析圖表類型
        if "圓餅圖" in text or "比例" in text:
            result["chart_type"] = "pie"
        elif "折線圖" in text or "趨勢" in text:
            result["chart_type"] = "line"
        elif "長條圖" in text or "柱狀圖" in text:
            result["chart_type"] = "bar"
        
        # 解析查詢類型
        if "趨勢" in text or "變化" in text:
            result["query_type"] = "trend"
        elif "比較" in text or "對比" in text:
            result["query_type"] = "compare"
        
        return result
    
    @classmethod
    def _extract_amount(cls, text: str) -> Optional[float]:
        """提取金額"""
        # 數字 + 元/塊/錢
        patterns = [
            r'(\d+(?:\.\d+)?)\s*[元塊錢]',
            r'\$\s*(\d+(?:\.\d+)?)',
            r'NT\$?\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:元|塊|錢|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        # 中文數字
        chinese_amount = cls._extract_chinese_amount(text)
        if chinese_amount:
            return chinese_amount
        
        # 最後嘗試匹配任何數字
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
        
        return None
    
    @classmethod
    def _extract_chinese_amount(cls, text: str) -> Optional[float]:
        """提取中文金額（如：五百塊、三千元）"""
        pattern = r'([零一二三四五六七八九十百千萬兩两]+)\s*[元塊錢]'
        match = re.search(pattern, text)
        if not match:
            return None
        
        chinese_num = match.group(1)
        return cls._chinese_to_number(chinese_num)
    
    @classmethod
    def _chinese_to_number(cls, text: str) -> float:
        """將中文數字轉為阿拉伯數字"""
        result = 0
        temp = 0
        
        for char in text:
            if char in cls.CHINESE_NUMS:
                num = cls.CHINESE_NUMS[char]
                if num >= 10:
                    if temp == 0:
                        temp = 1
                    temp *= num
                    if num >= 10000:
                        result += temp
                        temp = 0
                else:
                    temp = temp * 10 + num if temp >= 10 else num
        
        return float(result + temp)
    
    @classmethod
    def _extract_category(cls, text: str) -> Optional[str]:
        """提取類別"""
        # 使用 jieba 分詞
        words = list(jieba.cut(text))
        
        # 計算每個類別的匹配分數
        scores = {}
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            score = 0
            for word in words:
                for keyword in keywords:
                    if keyword in word or word in keyword:
                        score += 1
            if score > 0:
                scores[category] = score
        
        # 返回分數最高的類別
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    @classmethod
    def _clean_description(cls, text: str) -> str:
        """清理描述文字，移除金額和日期"""
        # 移除金額
        text = re.sub(r'\d+(?:\.\d+)?\s*[元塊錢]', '', text)
        text = re.sub(r'\$\s*\d+(?:\.\d+)?', '', text)
        text = re.sub(r'NT\$?\s*\d+(?:\.\d+)?', '', text, flags=re.IGNORECASE)
        
        # 移除日期關鍵字
        date_keywords = ['今天', '昨天', '前天', '今日', '昨日', '上週', '這週', '下週', '上個月', '這個月']
        for kw in date_keywords:
            text = text.replace(kw, '')
        
        # 清理多餘空白
        text = ' '.join(text.split())
        
        return text.strip()
    
    @classmethod
    def _parse_chinese_number(cls, text: str) -> int:
        """解析簡單中文數字"""
        if text.isdigit():
            return int(text)
        
        mapping = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
                   '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        
        if len(text) == 1:
            return mapping.get(text, 1)
        
        return 3  # 預設值


# 需要導入 timedelta
from datetime import timedelta
