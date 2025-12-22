"""
預算模型
支出上限設定與追蹤
"""

from datetime import date
from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class Budget(Base):
    """預算設定"""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # None = 總預算
    limit_amount = Column(Float, nullable=False)
    period = Column(String(10), nullable=False)  # "weekly" or "monthly"
    start_date = Column(Date, default=date.today)
    
    # 關聯
    category = relationship("Category", back_populates="budgets")
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "總預算",
            "category_icon": self.category.icon if self.category else "💳",
            "limit_amount": self.limit_amount,
            "period": self.period,
            "start_date": self.start_date.isoformat() if self.start_date else None
        }
