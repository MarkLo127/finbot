"""
對話模型
儲存 AI 對話上下文
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.types import JSON

from models.database import Base


class Conversation(Base):
    """對話上下文"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    context = Column(JSON, default=list)  # 對話歷史
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "context": self.context,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
