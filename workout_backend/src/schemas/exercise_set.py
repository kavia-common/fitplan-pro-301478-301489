from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from uuid import UUID


class ExerciseSetBase(BaseModel):
    """Base schema for ExerciseSet with common attributes."""
    workout_log_id: Optional[UUID] = Field(None, description="ID of the workout log")
    exercise_id: Optional[int] = Field(None, description="ID of the exercise")
    set_number: Optional[int] = Field(None, description="Set number in the workout")
    reps: Optional[int] = Field(None, description="Number of repetitions performed")
    weight_kg: Optional[Decimal] = Field(Decimal("0"), description="Weight used in kilograms")
    rpe: Optional[Decimal] = Field(None, description="Rate of Perceived Exertion (1-10)")


class ExerciseSetCreate(ExerciseSetBase):
    """Schema for creating a new exercise set."""
    pass


class ExerciseSetResponse(ExerciseSetBase):
    """Schema for ExerciseSet response with all fields."""
    id: int = Field(..., description="Unique exercise set identifier")

    model_config = ConfigDict(from_attributes=True)
