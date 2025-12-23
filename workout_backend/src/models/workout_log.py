from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.base import Base


class WorkoutLog(Base):
    """
    WorkoutLog model representing logged workout sessions.
    Maps to the 'workout_logs' table in the database.
    """
    __tablename__ = "workout_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=True, index=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_minutes = Column(Integer, default=0)

    # Relationships
    workout = relationship("Workout", back_populates="workout_logs")
    exercise_sets = relationship("ExerciseSet", back_populates="workout_log", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkoutLog(id={self.id}, workout_id={self.workout_id}, performed_at={self.performed_at})>"
