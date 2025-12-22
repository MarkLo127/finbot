"""
聊天 API 路由
處理記帳指令與對話
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from models.database import get_db
from models.transaction import Transaction
from models.category import Category
from models.conversation import Conversation
from services.nlp_parser import NLPParser
from services.ai_analyzer import AIAnalyzer


router = APIRouter()


class ChatMessage(BaseModel):
    """聊天訊息"""
    message: str
    source: str = "text"  # "text" 或 "voice"


class ChatResponse(BaseModel):
    """聊天回覆"""
    message: str
    type: str  # "confirmation", "query_result", "analysis", "error"
    data: Optional[Dict[str, Any]] = None


@router.post("/message", response_model=ChatResponse)
async def process_message(chat: ChatMessage, db: Session = Depends(get_db)):
    """
    處理聊天訊息
    
    自動判斷是記帳指令還是查詢/分析請求
    """
    text = chat.message.strip()
    
    if not text:
        return ChatResponse(
            message="請輸入訊息",
            type="error"
        )
    
    # 判斷意圖
    intent = _detect_intent(text)
    
    if intent == "record":
        # 記帳指令
        return await _handle_record(text, chat.source, db)
    elif intent == "query":
        # 查詢指令
        return await _handle_query(text, db)
    elif intent == "analysis":
        # 分析/對話
        return await _handle_analysis(text, db)
    else:
        # 預設嘗試記帳
        return await _handle_record(text, chat.source, db)


def _detect_intent(text: str) -> str:
    """偵測使用者意圖"""
    # 查詢關鍵字
    query_keywords = ["花了多少", "多少錢", "查詢", "統計", "報告", "報表", "趨勢", "分析圖"]
    for kw in query_keywords:
        if kw in text:
            return "query"
    
    # 分析/對話關鍵字
    analysis_keywords = ["是不是", "應該", "建議", "幫我", "為什麼", "怎麼", "如何"]
    for kw in analysis_keywords:
        if kw in text:
            return "analysis"
    
    # 記帳關鍵字（或包含數字）
    import re
    if re.search(r'\d+', text):
        return "record"
    
    return "analysis"


async def _handle_record(text: str, source: str, db: Session) -> ChatResponse:
    """處理記帳指令"""
    # 解析輸入
    parsed = NLPParser.parse(text)
    
    if not parsed["amount"]:
        return ChatResponse(
            message="抱歉，我無法識別金額。請用類似「午餐 120 元」的格式。",
            type="error"
        )
    
    # 查找類別
    category = db.query(Category).filter(Category.name == parsed["category"]).first()
    if not category:
        # 使用預設類別
        category = db.query(Category).filter(Category.name == "其他").first()
        if not category:
            category = db.query(Category).filter(Category.type == parsed["type"]).first()
    
    if not category:
        return ChatResponse(
            message="系統錯誤：找不到類別",
            type="error"
        )
    
    # 建立交易記錄
    transaction = Transaction(
        amount=parsed["amount"],
        type=parsed["type"],
        category_id=category.id,
        date=parsed["date"],
        description=parsed["description"],
        source=source
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # 計算本月該類別支出
    from datetime import date as date_type
    today = date_type.today()
    month_start = today.replace(day=1)
    
    monthly_total = db.query(Transaction).filter(
        Transaction.category_id == category.id,
        Transaction.date >= month_start,
        Transaction.type == "expense"
    ).with_entities(
        db.query(Transaction).column_descriptions[0]['entity'].amount
    ).all()
    
    monthly_sum = sum([t[0] for t in monthly_total]) if monthly_total else parsed["amount"]
    
    # 生成回覆
    type_text = "收入" if parsed["type"] == "income" else "支出"
    date_text = parsed["date"].strftime("%m/%d") if parsed["date"] != date_type.today() else "今天"
    
    message = f"✅ 已記錄{type_text}！\n\n"
    message += f"📝 {category.icon} {category.name}\n"
    message += f"💰 ${parsed['amount']:,.0f}\n"
    message += f"📅 {date_text}\n"
    
    if parsed["type"] == "expense":
        message += f"\n📊 本月{category.name}累計：${monthly_sum:,.0f}"
    
    return ChatResponse(
        message=message,
        type="confirmation",
        data=transaction.to_dict()
    )


async def _handle_query(text: str, db: Session) -> ChatResponse:
    """處理查詢指令"""
    # 解析查詢
    query = NLPParser.parse_query(text)
    
    # 查詢交易
    q = db.query(Transaction).filter(
        Transaction.date >= query["start_date"],
        Transaction.date <= query["end_date"]
    )
    
    if query["category"]:
        category = db.query(Category).filter(Category.name == query["category"]).first()
        if category:
            q = q.filter(Transaction.category_id == category.id)
    
    transactions = q.all()
    
    # 計算統計
    total = sum(t.amount for t in transactions if t.type == "expense")
    
    # 生成摘要
    if query["category"]:
        message = f"📊 {query['category']}支出查詢\n\n"
        message += f"📅 期間：{query['start_date']} ~ {query['end_date']}\n"
        message += f"💸 總金額：${total:,.0f}\n"
        message += f"📝 共 {len(transactions)} 筆交易"
    else:
        # 使用智慧摘要
        trans_dicts = [t.to_dict() for t in transactions]
        message = await AIAnalyzer.generate_smart_summary(trans_dicts, query["period"])
    
    return ChatResponse(
        message=message,
        type="query_result",
        data={
            "total": total,
            "count": len(transactions),
            "period": query["period"],
            "chart_type": query["chart_type"],
            "transactions": [t.to_dict() for t in transactions[:20]]  # 最多返回 20 筆
        }
    )


async def _handle_analysis(text: str, db: Session) -> ChatResponse:
    """處理 AI 分析請求"""
    # 取得近期交易
    from datetime import timedelta
    today = date.today()
    month_start = today.replace(day=1)
    
    transactions = db.query(Transaction).filter(
        Transaction.date >= month_start
    ).all()
    
    trans_dicts = [t.to_dict() for t in transactions]
    
    # AI 分析
    response = await AIAnalyzer.analyze_spending(trans_dicts, text)
    
    return ChatResponse(
        message=response,
        type="analysis"
    )


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """取得所有類別"""
    categories = db.query(Category).all()
    return [c.to_dict() for c in categories]
