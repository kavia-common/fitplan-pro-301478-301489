from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class WorkoutBase(BaseModel):
    """Base schema for Workout with common attributes."""
    user_id: Optional[UUID] = Field(None, description="ID of the user who owns this workout")
    goal: Optional[str] = Field(None, description="Workout goal (e.g., strength, endurance, weight loss)")


class WorkoutCreate(WorkoutBase):
    """Schema for creating a new workout."""
    pass


class WorkoutResponse(WorkoutBase):
    """Schema for Workout response with all fields."""
    id: UUID = Field(..., description="Unique workout identifier")
    created_at: datetime = Field(..., description="Timestamp when workout was created")

    model_config = ConfigDict(from_attributes=True)
