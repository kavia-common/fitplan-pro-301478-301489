from pydantic import BaseModel, Field, ConfigDict


class EquipmentBase(BaseModel):
    """Base schema for Equipment with common attributes."""
    name: str = Field(..., description="Equipment name")


class EquipmentCreate(EquipmentBase):
    """Schema for creating new equipment."""
    pass


class EquipmentResponse(EquipmentBase):
    """Schema for Equipment response with all fields."""
    id: int = Field(..., description="Unique equipment identifier")

    model_config = ConfigDict(from_attributes=True)
