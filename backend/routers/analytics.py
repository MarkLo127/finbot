"""
分析 API 路由 - 統計與圖表資料
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.transaction import Transaction
from services.ai_analyzer import AIAnalyzer

router = APIRouter()


@router.get("/summary")
async def get_summary(
    period: str = Query("month", regex="^(day|week|month|year)$"),
    db: Session = Depends(get_db)
):
    """取得期間摘要"""
    today = date.today()
    
    if period == "day":
        start = today
    elif period == "week":
        start = today - timedelta(days=today.weekday())
    elif period == "month":
        start = today.replace(day=1)
    else:
        start = today.replace(month=1, day=1)
    
    transactions = db.query(Transaction).filter(
        Transaction.date >= start, Transaction.date <= today
    ).all()
    
    total_expense = sum(t.amount for t in transactions if t.type == "expense")
    total_income = sum(t.amount for t in transactions if t.type == "income")
    
    by_category = {}
    for t in transactions:
        if t.type != "expense":
            continue
        cat_name = t.category.name if t.category else "其他"
        if cat_name not in by_category:
            by_category[cat_name] = {"name": cat_name, "icon": t.category.icon if t.category else "📦", "total": 0, "count": 0}
        by_category[cat_name]["total"] += t.amount
        by_category[cat_name]["count"] += 1
    
    return {
        "period": period, "start_date": start.isoformat(), "end_date": today.isoformat(),
        "total_expense": total_expense, "total_income": total_income,
        "net": total_income - total_expense, "transaction_count": len(transactions),
        "categories": sorted(by_category.values(), key=lambda x: x["total"], reverse=True)
    }


@router.get("/trend")
async def get_trend(months: int = Query(6, ge=1, le=12), category_id: Optional[int] = None, db: Session = Depends(get_db)):
    """取得趨勢資料"""
    today = date.today()
    start = today.replace(day=1)
    for _ in range(months - 1):
        start = (start - timedelta(days=1)).replace(day=1)
    
    query = db.query(Transaction).filter(Transaction.date >= start, Transaction.type == "expense")
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    transactions = query.all()
    monthly = {}
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + t.amount
    
    result = []
    current = start
    while current <= today:
        key = current.strftime("%Y-%m")
        result.append({"month": key, "label": current.strftime("%m月"), "amount": monthly.get(key, 0)})
        current = current.replace(month=current.month + 1) if current.month < 12 else current.replace(year=current.year + 1, month=1)
    
    return {"period_months": months, "data": result}


@router.get("/category-breakdown")
async def get_category_breakdown(start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = Depends(get_db)):
    """取得類別分佈（圓餅圖）"""
    today = date.today()
    start_date = start_date or today.replace(day=1)
    end_date = end_date or today
    
    transactions = db.query(Transaction).filter(
        Transaction.date >= start_date, Transaction.date <= end_date, Transaction.type == "expense"
    ).all()
    
    by_category = {}
    total = 0
    for t in transactions:
        cat_name = t.category.name if t.category else "其他"
        if cat_name not in by_category:
            by_category[cat_name] = {"name": cat_name, "icon": t.category.icon if t.category else "📦", "amount": 0}
        by_category[cat_name]["amount"] += t.amount
        total += t.amount
    
    result = []
    for cat in sorted(by_category.values(), key=lambda x: x["amount"], reverse=True):
        cat["percentage"] = round(cat["amount"] / total * 100, 1) if total > 0 else 0
        result.append(cat)
    
    return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "total": total, "categories": result}


@router.get("/insights")
async def get_insights(db: Session = Depends(get_db)):
    """取得智慧洞察"""
    today = date.today()
    transactions = db.query(Transaction).filter(Transaction.date >= today.replace(day=1)).all()
    trans_dicts = [t.to_dict() for t in transactions]
    summary = await AIAnalyzer.generate_smart_summary(trans_dicts, "month")
    return {"summary": summary, "insights": []}
