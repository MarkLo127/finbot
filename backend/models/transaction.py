"""
交易模型
記錄所有收入與支出
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class Transaction(Base):
    """交易記錄"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(10), nullable=False)  # "income" or "expense"
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(255), default="")
    source = Column(String(20), default="manual")  # "manual", "voice", "csv"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    category = relationship("Category", back_populates="transactions")
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.type,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "category_icon": self.category.icon if self.category else None,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
