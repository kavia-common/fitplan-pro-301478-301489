from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base


class ExerciseSet(Base):
    """
    ExerciseSet model representing individual sets within a workout log.
    Maps to the 'exercise_sets' table in the database.
    """
    __tablename__ = "exercise_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_log_id = Column(UUID(as_uuid=True), ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=True)
    set_number = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight_kg = Column(Numeric(10, 2), default=0)
    rpe = Column(Numeric(4, 1), nullable=True)

    # Relationships
    workout_log = relationship("WorkoutLog", back_populates="exercise_sets")
    exercise = relationship("Exercise", back_populates="exercise_sets")

    def __repr__(self):
        return f"<ExerciseSet(id={self.id}, exercise_id={self.exercise_id}, set_number={self.set_number})>"
