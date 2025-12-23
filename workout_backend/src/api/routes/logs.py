from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from src.database.connection import get_db
from src.models import WorkoutLog, ExerciseSet, Workout, Exercise, WorkoutExercise
from src.schemas.exercise_set import ExerciseSetResponse, ExerciseSetCreate
from pydantic import BaseModel, Field

router = APIRouter(tags=["logs"])


class WorkoutLogRequest(BaseModel):
    """Request schema for logging a workout session."""
    duration_minutes: int = Field(..., description="Duration of the workout in minutes", ge=1)


class ExerciseSetLogRequest(BaseModel):
    """Request schema for logging exercise sets."""
    sets: List[ExerciseSetCreate] = Field(..., description="List of sets performed")


class WorkoutLogDetailResponse(BaseModel):
    """Detailed workout log response with exercise sets."""
    log_id: UUID = Field(..., description="Workout log ID")
    workout_id: UUID = Field(..., description="Workout ID")
    performed_at: datetime = Field(..., description="When the workout was performed")
    duration_minutes: int = Field(..., description="Duration in minutes")
    exercise_sets: List[dict] = Field(..., description="Exercise sets logged")


# PUBLIC_INTERFACE
@router.post("/workouts/{workout_id}/log",
             response_model=WorkoutLogDetailResponse,
             summary="Log a workout session",
             description="Create a log entry for a completed workout session")
async def log_workout(
    workout_id: UUID,
    request: WorkoutLogRequest,
    db: Session = Depends(get_db)
) -> WorkoutLogDetailResponse:
    """
    Log a completed workout session.
    
    Creates a workout log entry that tracks when a workout was performed
    and its duration. This is the parent record for exercise set logs.
    
    Args:
        workout_id: ID of the workout being logged
        request: Workout log details
        db: Database session
        
    Returns:
        WorkoutLogDetailResponse: Created workout log with details
        
    Raises:
        HTTPException: 404 if workout not found, 400 if invalid data
    """
    # Validate workout exists
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Validate duration
    if request.duration_minutes < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be at least 1 minute"
        )
    
    # Create workout log
    workout_log = WorkoutLog(
        workout_id=workout_id,
        duration_minutes=request.duration_minutes
    )
    db.add(workout_log)
    db.commit()
    db.refresh(workout_log)
    
    return WorkoutLogDetailResponse(
        log_id=workout_log.id,
        workout_id=workout_log.workout_id,
        performed_at=workout_log.performed_at,
        duration_minutes=workout_log.duration_minutes,
        exercise_sets=[]
    )


# PUBLIC_INTERFACE
@router.post("/workouts/{workout_id}/exercises/{exercise_id}/log",
             response_model=List[ExerciseSetResponse],
             summary="Log exercise sets",
             description="Log the sets performed for a specific exercise in a workout session")
async def log_exercise_sets(
    workout_id: UUID,
    exercise_id: int,
    request: ExerciseSetLogRequest,
    db: Session = Depends(get_db)
) -> List[ExerciseSetResponse]:
    """
    Log exercise sets for a specific exercise.
    
    Records the details of each set performed (reps, weight, RPE) for an
    exercise within a workout session. Must have an active workout log.
    
    Args:
        workout_id: ID of the workout
        exercise_id: ID of the exercise
        request: Exercise set details
        db: Database session
        
    Returns:
        List[ExerciseSetResponse]: Created exercise set records
        
    Raises:
        HTTPException: 404 if workout/exercise not found, 400 if invalid data
    """
    # Validate workout exists
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Validate exercise exists and is part of this workout
    workout_exercise = db.query(WorkoutExercise).filter(
        WorkoutExercise.workout_id == workout_id,
        WorkoutExercise.exercise_id == exercise_id
    ).first()
    
    if not workout_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} is not part of workout {workout_id}"
        )
    
    # Validate exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    if not request.sets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one set must be provided"
        )
    
    # Get the most recent workout log for this workout
    workout_log = db.query(WorkoutLog).filter(
        WorkoutLog.workout_id == workout_id
    ).order_by(WorkoutLog.performed_at.desc()).first()
    
    if not workout_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active workout log found. Please log the workout session first using POST /workouts/{workout_id}/log"
        )
    
    # Create exercise sets
    created_sets = []
    for idx, set_data in enumerate(request.sets, start=1):
        exercise_set = ExerciseSet(
            workout_log_id=workout_log.id,
            exercise_id=exercise_id,
            set_number=idx,
            reps=set_data.reps,
            weight_kg=set_data.weight_kg,
            rpe=set_data.rpe
        )
        db.add(exercise_set)
        created_sets.append(exercise_set)
    
    db.commit()
    
    # Refresh all created sets
    for ex_set in created_sets:
        db.refresh(ex_set)
    
    return created_sets


# PUBLIC_INTERFACE
@router.get("/workouts/{workout_id}/logs",
            response_model=List[WorkoutLogDetailResponse],
            summary="Get logs for a workout",
            description="Retrieve all log entries for a specific workout with exercise details")
async def get_workout_logs(
    workout_id: UUID,
    db: Session = Depends(get_db)
) -> List[WorkoutLogDetailResponse]:
    """
    Get all logs for a specific workout.
    
    Args:
        workout_id: ID of the workout
        db: Database session
        
    Returns:
        List[WorkoutLogDetailResponse]: List of workout logs with exercise sets
        
    Raises:
        HTTPException: 404 if workout not found
    """
    # Validate workout exists
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with ID {workout_id} not found"
        )
    
    # Get all logs for this workout
    logs = db.query(WorkoutLog).filter(
        WorkoutLog.workout_id == workout_id
    ).order_by(WorkoutLog.performed_at.desc()).all()
    
    result = []
    for log in logs:
        # Get exercise sets for this log
        sets = db.query(ExerciseSet, Exercise).join(
            Exercise, ExerciseSet.exercise_id == Exercise.id
        ).filter(ExerciseSet.workout_log_id == log.id).all()
        
        exercise_sets = [
            {
                "set_id": ex_set.id,
                "exercise_id": ex_set.exercise_id,
                "exercise_name": exercise.name,
                "set_number": ex_set.set_number,
                "reps": ex_set.reps,
                "weight_kg": float(ex_set.weight_kg) if ex_set.weight_kg else 0,
                "rpe": float(ex_set.rpe) if ex_set.rpe else None
            }
            for ex_set, exercise in sets
        ]
        
        result.append(WorkoutLogDetailResponse(
            log_id=log.id,
            workout_id=log.workout_id,
            performed_at=log.performed_at,
            duration_minutes=log.duration_minutes,
            exercise_sets=exercise_sets
        ))
    
    return result
