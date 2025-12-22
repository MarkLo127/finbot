"""
日期解析器
處理相對日期與各種日期格式
"""

import re
from datetime import date, timedelta
from typing import Optional


class DateParser:
    """中文相對日期解析器"""
    
    # 中文數字對照
    CHINESE_NUMS = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '兩': 2, '两': 2
    }
    
    # 星期對照
    WEEKDAY_MAP = {
        '一': 0, '二': 1, '三': 2, '四': 3,
        '五': 4, '六': 5, '日': 6, '天': 6
    }
    
    @classmethod
    def parse(cls, text: str) -> Optional[date]:
        """
        解析日期文字
        
        支援格式：
        - 今天、昨天、前天
        - 上週五、這週三
        - 上個月15號
        - 12/20、12-20
        - 2024年12月20日
        """
        text = text.strip()
        today = date.today()
        
        # 相對日期
        if '今天' in text or '今日' in text:
            return today
        if '昨天' in text or '昨日' in text:
            return today - timedelta(days=1)
        if '前天' in text:
            return today - timedelta(days=2)
        if '大前天' in text:
            return today - timedelta(days=3)
        if '明天' in text or '明日' in text:
            return today + timedelta(days=1)
        
        # N天前
        match = re.search(r'(\d+|[一二三四五六七八九十]+)\s*天前', text)
        if match:
            days = cls._parse_chinese_number(match.group(1))
            return today - timedelta(days=days)
        
        # 上週X / 這週X / 下週X
        match = re.search(r'(上|這|下)週([一二三四五六日天])', text)
        if match:
            week_offset = {'上': -1, '這': 0, '下': 1}[match.group(1)]
            target_weekday = cls.WEEKDAY_MAP[match.group(2)]
            current_weekday = today.weekday()
            
            # 計算目標日期
            days_diff = target_weekday - current_weekday + (week_offset * 7)
            return today + timedelta(days=days_diff)
        
        # 上個月X號
        match = re.search(r'上個月(\d+)[號日]?', text)
        if match:
            day = int(match.group(1))
            first_of_month = today.replace(day=1)
            last_month = first_of_month - timedelta(days=1)
            try:
                return last_month.replace(day=day)
            except ValueError:
                return last_month
        
        # 這個月X號
        match = re.search(r'(這個月)?(\d+)[號日]', text)
        if match:
            day = int(match.group(2))
            try:
                return today.replace(day=day)
            except ValueError:
                return today
        
        # 日期格式：12/20 或 12-20
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})', text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                # 假設是今年
                return date(today.year, month, day)
            except ValueError:
                pass
        
        # 完整日期：2024年12月20日 或 2024/12/20
        match = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})[日]?', text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day)
            except ValueError:
                pass
        
        # 無法解析，返回今天
        return None
    
    @classmethod
    def _parse_chinese_number(cls, text: str) -> int:
        """解析中文數字"""
        if text.isdigit():
            return int(text)
        
        # 簡單的中文數字解析
        if len(text) == 1:
            return cls.CHINESE_NUMS.get(text, 1)
        
        # 處理 "十X" 或 "X十" 格式
        result = 0
        if '十' in text:
            parts = text.split('十')
            if parts[0]:
                result += cls.CHINESE_NUMS.get(parts[0], 1) * 10
            else:
                result += 10
            if len(parts) > 1 and parts[1]:
                result += cls.CHINESE_NUMS.get(parts[1], 0)
        else:
            for char in text:
                if char in cls.CHINESE_NUMS:
                    result = result * 10 + cls.CHINESE_NUMS[char]
        
        return result if result > 0 else 1
