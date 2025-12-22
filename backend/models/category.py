"""
類別模型
收入與支出的分類
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from models.database import Base


class Category(Base):
    """類別"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(10), default="📦")
    type = Column(String(10), nullable=False)  # "income" or "expense"
    
    # 關聯
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "type": self.type
        }
