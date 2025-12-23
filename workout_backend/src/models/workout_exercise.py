from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base


class WorkoutExercise(Base):
    """
    WorkoutExercise model representing exercises within a workout plan.
    Maps to the 'workout_exercises' table in the database.
    """
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=True)
    target_sets = Column(Integer, nullable=True)
    target_reps = Column(Integer, nullable=True)
    rest_seconds = Column(Integer, default=90)

    # Relationships
    workout = relationship("Workout", back_populates="workout_exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")

    def __repr__(self):
        return f"<WorkoutExercise(id={self.id}, workout_id={self.workout_id}, exercise_id={self.exercise_id})>"
