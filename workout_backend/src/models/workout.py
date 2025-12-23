from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.base import Base


class Workout(Base):
    """
    Workout model representing user workout plans.
    Maps to the 'workouts' table in the database.
    """
    __tablename__ = "workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    goal = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="workouts")
    workout_exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")
    workout_logs = relationship("WorkoutLog", back_populates="workout", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workout(id={self.id}, user_id={self.user_id}, goal={self.goal})>"
