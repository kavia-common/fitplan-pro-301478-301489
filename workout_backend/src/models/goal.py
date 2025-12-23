from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.base import Base


class Goal(Base):
    """
    Goal model representing user fitness goals.
    Maps to the 'goals' table in the database.
    """
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    goal_type = Column(Text, nullable=True)
    target_value = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<Goal(id={self.id}, user_id={self.user_id}, goal_type={self.goal_type})>"
