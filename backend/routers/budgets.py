"""
預算 API 路由
預算管理與追蹤
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.budget import Budget
from models.category import Category
from models.transaction import Transaction
from services.ai_analyzer import AIAnalyzer


router = APIRouter()


class BudgetCreate(BaseModel):
    """建立預算請求"""
    category_id: Optional[int] = None  # None = 總預算
    limit_amount: float
    period: str = "monthly"  # "weekly" or "monthly"


class BudgetUpdate(BaseModel):
    """更新預算請求"""
    limit_amount: Optional[float] = None
    period: Optional[str] = None


@router.get("")
async def list_budgets(db: Session = Depends(get_db)):
    """列出所有預算及其使用狀況"""
    budgets = db.query(Budget).all()
    result = []
    
    today = date.today()
    
    for budget in budgets:
        # 計算預算週期
        if budget.period == "weekly":
            start = today - timedelta(days=today.weekday())
        else:  # monthly
            start = today.replace(day=1)
        
        # 計算已使用金額
        query = db.query(func.sum(Transaction.amount)).filter(
            Transaction.date >= start,
            Transaction.date <= today,
            Transaction.type == "expense"
        )
        
        if budget.category_id:
            query = query.filter(Transaction.category_id == budget.category_id)
        
        used = query.scalar() or 0
        
        # 計算達成率
        rate = (used / budget.limit_amount * 100) if budget.limit_amount > 0 else 0
        
        result.append({
            **budget.to_dict(),
            "used": used,
            "remaining": max(0, budget.limit_amount - used),
            "rate": round(rate, 1),
            "status": "ok" if rate <= 80 else ("warning" if rate <= 100 else "exceeded")
        })
    
    return result


@router.get("/status")
async def get_budget_status(db: Session = Depends(get_db)):
    """取得預算警示狀態（用於通知）"""
    budgets = await list_budgets(db)
    
    warnings = []
    for b in budgets:
        if b["rate"] >= 80:
            warnings.append({
                "category": b["category_name"],
                "rate": b["rate"],
                "status": b["status"],
                "message": f"{b['category_name']}預算已使用 {b['rate']:.0f}%"
            })
    
    return {
        "has_warning": len(warnings) > 0,
        "warnings": warnings
    }


@router.get("/suggestion/{category_id}")
async def get_budget_suggestion(category_id: int, db: Session = Depends(get_db)):
    """取得 AI 預算建議"""
    # 取得類別
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="類別不存在")
    
    # 取得過去 6 個月的消費記錄
    today = date.today()
    six_months_ago = today.replace(day=1)
    for _ in range(6):
        six_months_ago = (six_months_ago - timedelta(days=1)).replace(day=1)
    
    transactions = db.query(Transaction).filter(
        Transaction.category_id == category_id,
        Transaction.date >= six_months_ago,
        Transaction.type == "expense"
    ).all()
    
    # 按月分組
    monthly_totals = {}
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        monthly_totals[key] = monthly_totals.get(key, 0) + t.amount
    
    history = [{"month": k, "amount": v} for k, v in monthly_totals.items()]
    
    # 取得 AI 建議
    suggestion = await AIAnalyzer.get_budget_suggestion(category.name, history)
    suggestion["category_name"] = category.name
    suggestion["category_icon"] = category.icon
    
    return suggestion


@router.post("", status_code=201)
async def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    """建立預算"""
    # 驗證類別（如果有指定）
    if data.category_id:
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="類別不存在")
        
        # 檢查是否已存在該類別的預算
        existing = db.query(Budget).filter(
            Budget.category_id == data.category_id,
            Budget.period == data.period
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="該類別已有相同週期的預算")
    
    budget = Budget(
        category_id=data.category_id,
        limit_amount=data.limit_amount,
        period=data.period,
        start_date=date.today()
    )
    
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    return budget.to_dict()


@router.put("/{budget_id}")
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db)
):
    """更新預算"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="預算不存在")
    
    if data.limit_amount is not None:
        budget.limit_amount = data.limit_amount
    if data.period is not None:
        budget.period = data.period
    
    db.commit()
    db.refresh(budget)
    
    return budget.to_dict()


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """刪除預算"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="預算不存在")
    
    db.delete(budget)
    db.commit()
    
    return None
