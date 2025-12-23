from sqlalchemy import Column, Integer, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from src.database.base import Base


class Exercise(Base):
    """
    Exercise model representing individual exercises.
    Maps to the 'exercises' table in the database.
    """
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False, index=True)
    primary_muscle = Column(Text, nullable=True, index=True)
    secondary_muscle = Column(Text, nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    calories_per_min = Column(Numeric(10, 2), default=5.00)

    # Relationships
    equipment = relationship("Equipment", back_populates="exercises")
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan")
    exercise_sets = relationship("ExerciseSet", back_populates="exercise", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exercise(id={self.id}, name={self.name}, primary_muscle={self.primary_muscle})>"
