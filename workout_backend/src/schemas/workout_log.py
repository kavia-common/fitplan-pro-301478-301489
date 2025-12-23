from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class WorkoutLogBase(BaseModel):
    """Base schema for WorkoutLog with common attributes."""
    workout_id: Optional[UUID] = Field(None, description="ID of the workout being logged")
    duration_minutes: Optional[int] = Field(0, description="Duration of workout in minutes")


class WorkoutLogCreate(WorkoutLogBase):
    """Schema for creating a new workout log."""
    pass


class WorkoutLogResponse(WorkoutLogBase):
    """Schema for WorkoutLog response with all fields."""
    id: UUID = Field(..., description="Unique workout log identifier")
    performed_at: datetime = Field(..., description="Timestamp when workout was performed")

    model_config = ConfigDict(from_attributes=True)
