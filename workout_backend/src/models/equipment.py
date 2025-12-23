from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from src.database.base import Base


class Equipment(Base):
    """
    Equipment model representing workout equipment types.
    Maps to the 'equipment' table in the database.
    """
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)

    # Relationships
    exercises = relationship("Exercise", back_populates="equipment")

    def __repr__(self):
        return f"<Equipment(id={self.id}, name={self.name})>"
