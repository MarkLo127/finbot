"""
資料庫連接與 ORM 設定
使用 SQLite + SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 資料庫路徑
DATABASE_URL = "sqlite:///./finbot.db"

# 建立引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 需要此設定
)

# Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基類
Base = declarative_base()


def get_db():
    """取得資料庫 Session（依賴注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """建立所有資料表"""
    from models.transaction import Transaction
    from models.category import Category
    from models.budget import Budget
    from models.conversation import Conversation
    
    Base.metadata.create_all(bind=engine)
    
    # 初始化預設類別
    _init_default_categories()


def _init_default_categories():
    """初始化預設類別"""
    from models.category import Category
    
    db = SessionLocal()
    try:
        # 檢查是否已有類別
        if db.query(Category).count() > 0:
            return
        
        # 預設支出類別
        expense_categories = [
            ("餐飲", "🍔", "expense"),
            ("交通", "🚗", "expense"),
            ("娛樂", "🎮", "expense"),
            ("購物", "🛒", "expense"),
            ("醫療", "💊", "expense"),
            ("居住", "🏠", "expense"),
            ("教育", "📚", "expense"),
            ("其他", "📦", "expense"),
        ]
        
        # 預設收入類別
        income_categories = [
            ("薪資", "💰", "income"),
            ("投資", "📈", "income"),
            ("其他收入", "💵", "income"),
        ]
        
        for name, icon, type_ in expense_categories + income_categories:
            category = Category(name=name, icon=icon, type=type_)
            db.add(category)
        
        db.commit()
    finally:
        db.close()
