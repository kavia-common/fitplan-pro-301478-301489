from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID


class WorkoutExerciseBase(BaseModel):
    """Base schema for WorkoutExercise with common attributes."""
    workout_id: Optional[UUID] = Field(None, description="ID of the workout")
    exercise_id: Optional[int] = Field(None, description="ID of the exercise")
    target_sets: Optional[int] = Field(None, description="Target number of sets")
    target_reps: Optional[int] = Field(None, description="Target number of reps per set")
    rest_seconds: Optional[int] = Field(90, description="Rest time between sets in seconds")


class WorkoutExerciseCreate(WorkoutExerciseBase):
    """Schema for creating a new workout exercise."""
    pass


class WorkoutExerciseResponse(WorkoutExerciseBase):
    """Schema for WorkoutExercise response with all fields."""
    id: int = Field(..., description="Unique workout exercise identifier")

    model_config = ConfigDict(from_attributes=True)
