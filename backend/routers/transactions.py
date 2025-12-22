"""
交易 API 路由
CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session

from models.database import get_db
from models.transaction import Transaction
from models.category import Category


router = APIRouter()


class TransactionCreate(BaseModel):
    """建立交易請求"""
    amount: float
    type: str  # "income" or "expense"
    category_id: int
    date: date
    description: Optional[str] = ""
    source: str = "manual"


class TransactionUpdate(BaseModel):
    """更新交易請求"""
    amount: Optional[float] = None
    type: Optional[str] = None
    category_id: Optional[int] = None
    date: Optional[date] = None
    description: Optional[str] = None


@router.get("")
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    列出交易記錄
    
    支援分頁與篩選
    """
    query = db.query(Transaction)
    
    if type:
        query = query.filter(Transaction.type == type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    total = query.count()
    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc())\
                       .offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [t.to_dict() for t in transactions]
    }


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """取得單筆交易"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    return transaction.to_dict()


@router.post("", status_code=201)
async def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """建立交易"""
    # 驗證類別
    category = db.query(Category).filter(Category.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="類別不存在")
    
    transaction = Transaction(
        amount=data.amount,
        type=data.type,
        category_id=data.category_id,
        date=data.date,
        description=data.description,
        source=data.source
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction.to_dict()


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """更新交易"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    if data.amount is not None:
        transaction.amount = data.amount
    if data.type is not None:
        transaction.type = data.type
    if data.category_id is not None:
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="類別不存在")
        transaction.category_id = data.category_id
    if data.date is not None:
        transaction.date = data.date
    if data.description is not None:
        transaction.description = data.description
    
    db.commit()
    db.refresh(transaction)
    
    return transaction.to_dict()


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """刪除交易"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    db.delete(transaction)
    db.commit()
    
    return None
