from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal


class ExerciseBase(BaseModel):
    """Base schema for Exercise with common attributes."""
    name: str = Field(..., description="Exercise name")
    primary_muscle: Optional[str] = Field(None, description="Primary muscle group targeted")
    secondary_muscle: Optional[str] = Field(None, description="Secondary muscle group targeted")
    equipment_id: Optional[int] = Field(None, description="ID of required equipment")
    calories_per_min: Optional[Decimal] = Field(Decimal("5.00"), description="Calories burned per minute")


class ExerciseCreate(ExerciseBase):
    """Schema for creating a new exercise."""
    pass


class ExerciseResponse(ExerciseBase):
    """Schema for Exercise response with all fields."""
    id: int = Field(..., description="Unique exercise identifier")

    model_config = ConfigDict(from_attributes=True)
