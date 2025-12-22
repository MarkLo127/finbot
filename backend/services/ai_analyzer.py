"""
AI 分析器（純離線版）
使用規則引擎提供智慧分析、建議與摘要功能
"""

from typing import Dict, Any, List
from datetime import date


class AIAnalyzer:
    """AI 分析引擎（規則引擎實作）"""

    @classmethod
    async def analyze_spending(cls, transactions: List[Dict], question: str) -> str:
        """
        分析消費並回答問題
        
        Args:
            transactions: 交易記錄列表
            question: 使用者問題
        
        Returns:
            分析回覆
        """
        if not transactions:
            return "目前沒有足夠的數據進行分析。請先記錄一些消費！"
        
        total = sum(t["amount"] for t in transactions if t.get("type") == "expense")
        count = len([t for t in transactions if t.get("type") == "expense"])
        avg = total / count if count > 0 else 0
        
        # 按類別統計
        by_category = {}
        for t in transactions:
            if t.get("type") != "expense":
                continue
            cat = t.get("category_name", "其他")
            by_category[cat] = by_category.get(cat, 0) + t["amount"]
        
        top_category = max(by_category, key=by_category.get) if by_category else "無"
        top_amount = by_category.get(top_category, 0)
        
        # 根據問題關鍵字生成回覆
        question_lower = question.lower()
        
        if "外食" in question or "餐飲" in question:
            food = by_category.get("餐飲", 0)
            percentage = (food / total * 100) if total > 0 else 0
            if percentage > 40:
                return f"📊 您的餐飲支出為 ${food:,.0f}，佔總支出 {percentage:.1f}%，確實偏高！\n\n💡 建議：可以嘗試每週自己煮 2-3 餐，預估可節省 30% 餐飲開支。"
            else:
                return f"📊 您的餐飲支出為 ${food:,.0f}，佔總支出 {percentage:.1f}%，比例尚可。"
        
        if "節省" in question or "省錢" in question or "省" in question:
            suggestions = []
            sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            
            for cat, amount in sorted_cats[:3]:
                percentage = (amount / total * 100) if total > 0 else 0
                if percentage > 25:
                    suggestions.append(f"• {cat}：${amount:,.0f}（{percentage:.1f}%）- 可優先檢視")
            
            if suggestions:
                return f"💡 **節省建議**\n\n以下類別佔比較高，建議優先審視：\n\n" + "\n".join(suggestions)
            else:
                return f"✅ 您的消費分佈相對均勻，目前沒有明顯可大幅節省的類別。繼續保持！"
        
        if "趨勢" in question or "變化" in question:
            return f"📈 您共有 {count} 筆支出，總金額 ${total:,.0f}，平均每筆 ${avg:,.0f}。\n\n最大支出類別：{top_category}（${top_amount:,.0f}）"
        
        if "多" in question or "太多" in question:
            for cat in by_category:
                if cat in question:
                    amount = by_category[cat]
                    percentage = (amount / total * 100) if total > 0 else 0
                    if percentage > 30:
                        return f"⚠️ 是的，{cat}支出 ${amount:,.0f} 佔了 {percentage:.1f}%，確實較高。建議設置預算上限來控制。"
                    else:
                        return f"📊 {cat}支出 ${amount:,.0f}，佔 {percentage:.1f}%，比例還算正常。"
        
        # 預設回覆
        return f"📊 **消費分析**\n\n• 總支出：${total:,.0f}\n• 交易筆數：{count} 筆\n• 平均每筆：${avg:,.0f}\n• 最大類別：{top_category}（${top_amount:,.0f}）\n\n💡 有什麼具體想了解的嗎？例如：「餐飲花太多嗎」「怎麼省錢」"
    
    @classmethod
    async def get_budget_suggestion(cls, category: str, history: List[Dict]) -> Dict[str, Any]:
        """
        取得預算建議
        
        Args:
            category: 類別名稱
            history: 歷史消費記錄（按月統計）
        
        Returns:
            預算建議
        """
        if not history:
            return {
                "suggested_amount": 0,
                "confidence": 0,
                "reason": "沒有足夠的歷史數據來建議預算"
            }
        
        # 計算統計數據
        amounts = [t.get("amount", 0) for t in history]
        avg = sum(amounts) / len(amounts)
        max_val = max(amounts)
        min_val = min(amounts)
        
        # 建議預算為平均值的 110%（留有餘裕）
        suggested = round(avg * 1.1, -1)  # 四捨五入到十位
        
        # 信心度基於資料量
        confidence = min(len(history) / 6, 1.0)
        
        return {
            "suggested_amount": suggested,
            "average": round(avg, 0),
            "min": min_val,
            "max": max_val,
            "confidence": confidence,
            "reason": f"根據過去 {len(history)} 個月，平均消費 ${avg:,.0f}，建議預算 ${suggested:,.0f}（含 10% 緩衝）"
        }
    
    @classmethod
    async def generate_smart_summary(cls, transactions: List[Dict], period: str = "month") -> str:
        """
        生成智慧摘要
        
        Args:
            transactions: 交易記錄
            period: 時間週期
        
        Returns:
            摘要文字
        """
        if not transactions:
            return "📭 這段期間沒有任何交易記錄。"
        
        # 計算統計
        expenses = [t for t in transactions if t.get("type") == "expense"]
        incomes = [t for t in transactions if t.get("type") == "income"]
        
        total_expense = sum(t["amount"] for t in expenses)
        total_income = sum(t["amount"] for t in incomes)
        net = total_income - total_expense
        
        # 按類別分組（僅支出）
        by_category = {}
        for t in expenses:
            cat = t.get("category_name", "其他")
            icon = t.get("category_icon", "📦")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "count": 0, "icon": icon}
            by_category[cat]["total"] += t["amount"]
            by_category[cat]["count"] += 1
        
        # 排序
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1]["total"], reverse=True)
        
        # 生成摘要
        period_text = {
            "day": "今天", 
            "week": "本週", 
            "month": "本月", 
            "year": "今年"
        }.get(period, "這段期間")
        
        lines = [
            f"📊 **{period_text}財務摘要**",
            "",
            f"💸 總支出：${total_expense:,.0f}",
            f"💰 總收入：${total_income:,.0f}",
        ]
        
        if net >= 0:
            lines.append(f"✅ 淨額：+${net:,.0f}")
        else:
            lines.append(f"⚠️ 淨額：-${abs(net):,.0f}")
        
        if sorted_cats:
            lines.append("")
            lines.append("📋 **支出分佈**")
            for cat, data in sorted_cats[:5]:
                percentage = (data["total"] / total_expense * 100) if total_expense > 0 else 0
                lines.append(f"{data['icon']} {cat}：${data['total']:,.0f}（{percentage:.0f}%）")
        
        # 加入小提示
        if sorted_cats and total_expense > 0:
            top_cat = sorted_cats[0][0]
            top_pct = (sorted_cats[0][1]["total"] / total_expense * 100)
            if top_pct > 40:
                lines.append("")
                lines.append(f"💡 提示：{top_cat}佔比超過 40%，可考慮設置預算控制")
        
        return "\n".join(lines)
