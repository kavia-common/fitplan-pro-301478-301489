from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's full name")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserResponse(UserBase):
    """Schema for User response with all fields."""
    id: UUID = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="Timestamp when user was created")

    model_config = ConfigDict(from_attributes=True)
