"""
匯入匯出 API 路由 - CSV 匯入與 PDF 報表匯出
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
import pandas as pd
from io import StringIO

from models.database import get_db
from models.transaction import Transaction
from models.category import Category
from models.budget import Budget
from services.nlp_parser import NLPParser
from services.report_generator import ReportGenerator

router = APIRouter()


@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    auto_categorize: bool = Query(True, description="是否自動分類"),
    db: Session = Depends(get_db)
):
    """匯入 CSV 交易記錄"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="請上傳 CSV 檔案")
    
    content = await file.read()
    try:
        df = pd.read_csv(StringIO(content.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 解析錯誤: {str(e)}")
    
    # 標準化欄位名稱
    column_mapping = {
        '日期': 'date', '金額': 'amount', '描述': 'description', '說明': 'description',
        '類別': 'category', '摘要': 'description', 'Date': 'date', 'Amount': 'amount'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    required = ['date', 'amount']
    for col in required:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"缺少必要欄位: {col}")
    
    imported = 0
    errors = []
    default_category = db.query(Category).filter(Category.name == "其他").first()
    
    for idx, row in df.iterrows():
        try:
            amount = abs(float(row['amount']))
            trans_type = "expense" if float(row['amount']) < 0 else "income"
            trans_date = pd.to_datetime(row['date']).date()
            description = str(row.get('description', ''))
            
            # 自動分類
            category = default_category
            if auto_categorize and description:
                parsed = NLPParser.parse(description)
                if parsed["category"]:
                    cat = db.query(Category).filter(Category.name == parsed["category"]).first()
                    if cat:
                        category = cat
            
            transaction = Transaction(
                amount=amount, type=trans_type, category_id=category.id,
                date=trans_date, description=description, source="csv"
            )
            db.add(transaction)
            imported += 1
        except Exception as e:
            errors.append(f"第 {idx + 2} 行: {str(e)}")
    
    db.commit()
    
    return {
        "success": True, "imported": imported,
        "errors": errors[:10] if errors else [],
        "message": f"成功匯入 {imported} 筆交易" + (f"，{len(errors)} 筆失敗" if errors else "")
    }


@router.get("/export/pdf")
async def export_pdf(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """匯出月度 PDF 報表"""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    transactions = db.query(Transaction).filter(
        Transaction.date >= start_date, Transaction.date < end_date
    ).all()
    
    budgets = db.query(Budget).all()
    
    trans_dicts = [t.to_dict() for t in transactions]
    budget_dicts = [b.to_dict() for b in budgets]
    
    pdf_bytes = ReportGenerator.generate_monthly_report(trans_dicts, budget_dicts, year, month)
    
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{year}_{month:02d}.pdf"}
    )


@router.get("/export/csv")
async def export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """匯出 CSV"""
    query = db.query(Transaction)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    lines = ["日期,類別,描述,金額,類型"]
    for t in transactions:
        cat_name = t.category.name if t.category else "其他"
        amount = t.amount if t.type == "income" else -t.amount
        lines.append(f"{t.date},{cat_name},{t.description},{amount},{t.type}")
    
    csv_content = "\n".join(lines)
    
    return Response(
        content=csv_content.encode('utf-8-sig'), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )
