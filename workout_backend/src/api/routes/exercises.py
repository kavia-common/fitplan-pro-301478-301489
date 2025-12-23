from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.connection import get_db
from src.models import Exercise, Equipment
from src.schemas.exercise import ExerciseResponse

router = APIRouter(prefix="/exercises", tags=["exercises"])


# PUBLIC_INTERFACE
@router.get("",
            response_model=List[ExerciseResponse],
            summary="Get all exercises",
            description="Retrieve all exercises with optional filtering by muscle group and equipment")
async def get_exercises(
    primary_muscle: Optional[str] = Query(None, description="Filter by primary muscle group"),
    equipment: Optional[str] = Query(None, description="Filter by equipment name"),
    db: Session = Depends(get_db)
) -> List[ExerciseResponse]:
    """
    Get all exercises with optional filtering.
    
    This endpoint retrieves the exercise library with optional filters:
    - Filter by primary muscle group (e.g., 'chest', 'back', 'legs')
    - Filter by equipment type (e.g., 'Barbell', 'Dumbbell', 'Bodyweight')
    
    Args:
        primary_muscle: Optional muscle group filter
        equipment: Optional equipment name filter
        db: Database session
        
    Returns:
        List[ExerciseResponse]: List of exercises matching the criteria
    """
    query = db.query(Exercise)
    
    # Apply filters
    if primary_muscle:
        query = query.filter(Exercise.primary_muscle.ilike(f"%{primary_muscle}%"))
    
    if equipment:
        # Get equipment ID
        equipment_obj = db.query(Equipment).filter(Equipment.name.ilike(f"%{equipment}%")).first()
        if equipment_obj:
            query = query.filter(Exercise.equipment_id == equipment_obj.id)
        else:
            # If equipment not found, return empty list
            return []
    
    exercises = query.order_by(Exercise.name).all()
    
    return exercises


# PUBLIC_INTERFACE
@router.get("/{exercise_id}",
            response_model=ExerciseResponse,
            summary="Get exercise by ID",
            description="Retrieve detailed information about a specific exercise")
async def get_exercise_by_id(
    exercise_id: int,
    db: Session = Depends(get_db)
) -> ExerciseResponse:
    """
    Get a specific exercise by ID.
    
    Args:
        exercise_id: Exercise ID
        db: Database session
        
    Returns:
        ExerciseResponse: Exercise details
        
    Raises:
        HTTPException: 404 if exercise not found
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    return exercise
