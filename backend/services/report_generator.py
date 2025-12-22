"""
報表生成器
生成 PDF 月度報表
"""

from io import BytesIO
from datetime import date
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart


class ReportGenerator:
    """PDF 報表生成器"""
    
    @classmethod
    def generate_monthly_report(
        cls,
        transactions: List[Dict],
        budgets: List[Dict],
        year: int,
        month: int
    ) -> bytes:
        """
        生成月度 PDF 報表
        
        Args:
            transactions: 該月交易記錄
            budgets: 預算設定
            year: 年份
            month: 月份
        
        Returns:
            PDF 檔案內容（bytes）
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 建立樣式
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # 置中
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10
        )
        normal_style = styles['Normal']
        
        elements = []
        
        # 標題
        elements.append(Paragraph(f"{year}年{month}月 財務報表", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # 摘要統計
        elements.append(Paragraph("📊 摘要統計", heading_style))
        summary = cls._calculate_summary(transactions)
        summary_data = [
            ["項目", "金額"],
            ["總支出", f"${summary['total_expense']:,.0f}"],
            ["總收入", f"${summary['total_income']:,.0f}"],
            ["淨額", f"${summary['net']:,.0f}"],
            ["交易筆數", f"{summary['count']} 筆"],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90A4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 類別分析
        elements.append(Paragraph("📋 支出類別分析", heading_style))
        by_category = cls._group_by_category(transactions)
        if by_category:
            cat_data = [["類別", "金額", "佔比", "筆數"]]
            total_expense = summary['total_expense'] or 1
            for cat, data in sorted(by_category.items(), key=lambda x: x[1]['total'], reverse=True):
                percentage = (data['total'] / total_expense * 100)
                cat_data.append([
                    cat,
                    f"${data['total']:,.0f}",
                    f"{percentage:.1f}%",
                    str(data['count'])
                ])
            
            cat_table = Table(cat_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B8E23')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
            ]))
            elements.append(cat_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 預算達成率
        if budgets:
            elements.append(Paragraph("🎯 預算達成率", heading_style))
            budget_data = [["類別", "預算", "已使用", "達成率"]]
            
            for budget in budgets:
                cat_name = budget.get('category_name', '總預算')
                limit = budget.get('limit_amount', 0)
                used = by_category.get(cat_name, {}).get('total', 0) if cat_name != '總預算' else summary['total_expense']
                rate = (used / limit * 100) if limit > 0 else 0
                
                status = "✅" if rate <= 80 else ("⚠️" if rate <= 100 else "❌")
                budget_data.append([
                    f"{status} {cat_name}",
                    f"${limit:,.0f}",
                    f"${used:,.0f}",
                    f"{rate:.1f}%"
                ])
            
            budget_table = Table(budget_data, colWidths=[2*inch, 1.3*inch, 1.3*inch, 1*inch])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CD853F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
            ]))
            elements.append(budget_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # 異常消費提示
        anomalies = cls._detect_anomalies(transactions)
        if anomalies:
            elements.append(Paragraph("⚠️ 異常消費提示", heading_style))
            for anomaly in anomalies:
                elements.append(Paragraph(f"• {anomaly}", normal_style))
            elements.append(Spacer(1, 0.3*inch))
        
        # 交易明細（最近 20 筆）
        elements.append(Paragraph("📝 交易明細（最近 20 筆）", heading_style))
        if transactions:
            detail_data = [["日期", "類別", "描述", "金額"]]
            for t in sorted(transactions, key=lambda x: x.get('date', ''), reverse=True)[:20]:
                amount_str = f"${t['amount']:,.0f}"
                if t.get('type') == 'income':
                    amount_str = f"+{amount_str}"
                else:
                    amount_str = f"-{amount_str}"
                
                detail_data.append([
                    t.get('date', '')[:10] if t.get('date') else '',
                    t.get('category_name', ''),
                    (t.get('description', '')[:15] + '...' if len(t.get('description', '')) > 15 else t.get('description', '')),
                    amount_str
                ])
            
            detail_table = Table(detail_data, colWidths=[1.2*inch, 1.2*inch, 2*inch, 1.2*inch])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#708090')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ]))
            elements.append(detail_table)
        
        # 頁尾
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph(
            f"報表生成日期：{date.today().isoformat()} | FinBot 財務助理",
            footer_style
        ))
        
        # 建立 PDF
        doc.build(elements)
        
        return buffer.getvalue()
    
    @classmethod
    def _calculate_summary(cls, transactions: List[Dict]) -> Dict[str, Any]:
        """計算摘要統計"""
        total_expense = sum(t['amount'] for t in transactions if t.get('type') == 'expense')
        total_income = sum(t['amount'] for t in transactions if t.get('type') == 'income')
        
        return {
            "total_expense": total_expense,
            "total_income": total_income,
            "net": total_income - total_expense,
            "count": len(transactions)
        }
    
    @classmethod
    def _group_by_category(cls, transactions: List[Dict]) -> Dict[str, Dict]:
        """按類別分組"""
        result = {}
        for t in transactions:
            if t.get('type') != 'expense':
                continue
            cat = t.get('category_name', '其他')
            if cat not in result:
                result[cat] = {'total': 0, 'count': 0}
            result[cat]['total'] += t['amount']
            result[cat]['count'] += 1
        return result
    
    @classmethod
    def _detect_anomalies(cls, transactions: List[Dict]) -> List[str]:
        """偵測異常消費"""
        anomalies = []
        
        if not transactions:
            return anomalies
        
        # 計算平均值
        amounts = [t['amount'] for t in transactions if t.get('type') == 'expense']
        if not amounts:
            return anomalies
        
        avg = sum(amounts) / len(amounts)
        
        # 檢測高額消費（超過平均 3 倍）
        for t in transactions:
            if t.get('type') == 'expense' and t['amount'] > avg * 3:
                anomalies.append(
                    f"高額消費：{t.get('description', '未命名')} ${t['amount']:,.0f}（超過平均 {t['amount']/avg:.1f} 倍）"
                )
        
        # 檢測重複消費（同一天相同金額超過 2 次）
        from collections import defaultdict
        daily_amounts = defaultdict(list)
        for t in transactions:
            if t.get('type') == 'expense':
                key = (t.get('date', ''), t['amount'])
                daily_amounts[key].append(t)
        
        for key, items in daily_amounts.items():
            if len(items) >= 2:
                anomalies.append(
                    f"短時間重複消費：{key[0]} 有 {len(items)} 筆相同金額 ${key[1]:,.0f}"
                )
        
        return anomalies[:5]  # 最多顯示 5 個異常
