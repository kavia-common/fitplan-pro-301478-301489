from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class GoalBase(BaseModel):
    """Base schema for Goal with common attributes."""
    user_id: Optional[UUID] = Field(None, description="ID of the user who owns this goal")
    goal_type: Optional[str] = Field(None, description="Type of goal (e.g., weight loss, muscle gain)")
    target_value: Optional[Decimal] = Field(None, description="Target value for the goal")


class GoalCreate(GoalBase):
    """Schema for creating a new goal."""
    pass


class GoalResponse(GoalBase):
    """Schema for Goal response with all fields."""
    id: int = Field(..., description="Unique goal identifier")
    created_at: datetime = Field(..., description="Timestamp when goal was created")

    model_config = ConfigDict(from_attributes=True)
