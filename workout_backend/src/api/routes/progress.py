from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from src.database.connection import get_db
from src.models import User, Workout, WorkoutLog, ExerciseSet, Exercise
from pydantic import BaseModel, Field

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressSummary(BaseModel):
    """Progress summary response."""
    user_id: UUID = Field(..., description="User ID")
    total_workouts: int = Field(..., description="Total number of workouts completed")
    total_exercises: int = Field(..., description="Total number of exercises performed")
    total_sets: int = Field(..., description="Total number of sets completed")
    total_reps: int = Field(..., description="Total number of reps performed")
    total_duration_minutes: int = Field(..., description="Total workout time in minutes")
    estimated_calories_burned: float = Field(..., description="Estimated total calories burned")
    workout_frequency: dict = Field(..., description="Workout frequency by time period")
    exercise_progress: List[dict] = Field(..., description="Progress per exercise")


class ExerciseProgress(BaseModel):
    """Progress tracking for a specific exercise."""
    exercise_id: int = Field(..., description="Exercise ID")
    exercise_name: str = Field(..., description="Exercise name")
    total_sets: int = Field(..., description="Total sets completed")
    total_reps: int = Field(..., description="Total reps performed")
    max_weight_kg: float = Field(..., description="Maximum weight lifted")
    avg_weight_kg: float = Field(..., description="Average weight lifted")
    progression: List[dict] = Field(..., description="Historical progression data")


# PUBLIC_INTERFACE
@router.get("",
            response_model=ProgressSummary,
            summary="Get user progress summary",
            description="Retrieve comprehensive progress statistics for a user")
async def get_progress_summary(
    user_id: UUID,
    days: int = Query(30, description="Number of days to include in the summary", ge=1, le=365),
    db: Session = Depends(get_db)
) -> ProgressSummary:
    """
    Get comprehensive progress summary for a user.
    
    Calculates and returns:
    - Total workouts completed
    - Total exercises, sets, and reps
    - Total workout duration
    - Estimated calories burned
    - Workout frequency trends
    - Per-exercise progress
    
    Args:
        user_id: User ID
        days: Number of days to include in summary (default 30)
        db: Database session
        
    Returns:
        ProgressSummary: Comprehensive progress statistics
        
    Raises:
        HTTPException: 404 if user not found
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get all workouts for the user
    workouts = db.query(Workout).filter(Workout.user_id == user_id).all()
    workout_ids = [w.id for w in workouts]
    
    if not workout_ids:
        return ProgressSummary(
            user_id=user_id,
            total_workouts=0,
            total_exercises=0,
            total_sets=0,
            total_reps=0,
            total_duration_minutes=0,
            estimated_calories_burned=0.0,
            workout_frequency={"last_7_days": 0, "last_30_days": 0, "last_90_days": 0},
            exercise_progress=[]
        )
    
    # Get workout logs within date range
    logs = db.query(WorkoutLog).filter(
        WorkoutLog.workout_id.in_(workout_ids),
        WorkoutLog.performed_at >= start_date
    ).all()
    
    log_ids = [log.id for log in logs]
    
    # Calculate basic stats
    total_workouts = len(logs)
    total_duration = sum(log.duration_minutes for log in logs)
    
    # Get exercise sets
    if log_ids:
        sets = db.query(ExerciseSet).filter(
            ExerciseSet.workout_log_id.in_(log_ids)
        ).all()
    else:
        sets = []
    
    total_sets = len(sets)
    total_reps = sum(s.reps or 0 for s in sets)
    
    # Count unique exercises
    unique_exercises = len(set(s.exercise_id for s in sets if s.exercise_id))
    
    # Estimate calories burned (rough estimate based on duration)
    # Average of 5-8 calories per minute depending on intensity
    estimated_calories = total_duration * 6.5
    
    # Calculate workout frequency
    now = datetime.utcnow()
    logs_7_days = sum(1 for log in logs if log.performed_at >= now - timedelta(days=7))
    logs_30_days = sum(1 for log in logs if log.performed_at >= now - timedelta(days=30))
    logs_90_days = sum(1 for log in logs if log.performed_at >= now - timedelta(days=90))
    
    workout_frequency = {
        "last_7_days": logs_7_days,
        "last_30_days": logs_30_days,
        "last_90_days": logs_90_days
    }
    
    # Calculate per-exercise progress
    exercise_progress = []
    exercise_sets_map = {}
    
    for ex_set in sets:
        if ex_set.exercise_id:
            if ex_set.exercise_id not in exercise_sets_map:
                exercise_sets_map[ex_set.exercise_id] = []
            exercise_sets_map[ex_set.exercise_id].append(ex_set)
    
    for exercise_id, ex_sets in exercise_sets_map.items():
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            continue
        
        weights = [float(s.weight_kg) for s in ex_sets if s.weight_kg]
        
        exercise_progress.append({
            "exercise_id": exercise_id,
            "exercise_name": exercise.name,
            "total_sets": len(ex_sets),
            "total_reps": sum(s.reps or 0 for s in ex_sets),
            "max_weight_kg": max(weights) if weights else 0.0,
            "avg_weight_kg": sum(weights) / len(weights) if weights else 0.0
        })
    
    # Sort by total sets descending
    exercise_progress.sort(key=lambda x: x["total_sets"], reverse=True)
    
    return ProgressSummary(
        user_id=user_id,
        total_workouts=total_workouts,
        total_exercises=unique_exercises,
        total_sets=total_sets,
        total_reps=total_reps,
        total_duration_minutes=total_duration,
        estimated_calories_burned=round(estimated_calories, 2),
        workout_frequency=workout_frequency,
        exercise_progress=exercise_progress
    )


# PUBLIC_INTERFACE
@router.get("/exercise/{exercise_id}",
            response_model=ExerciseProgress,
            summary="Get exercise-specific progress",
            description="Track progress for a specific exercise with historical data")
async def get_exercise_progress(
    user_id: UUID,
    exercise_id: int,
    days: int = Query(90, description="Number of days of history to retrieve", ge=1, le=365),
    db: Session = Depends(get_db)
) -> ExerciseProgress:
    """
    Get detailed progress for a specific exercise.
    
    Provides historical tracking of weight, reps, and performance over time
    for progressive overload monitoring.
    
    Args:
        user_id: User ID
        exercise_id: Exercise ID
        days: Number of days of history (default 90)
        db: Database session
        
    Returns:
        ExerciseProgress: Detailed exercise progress with historical data
        
    Raises:
        HTTPException: 404 if user or exercise not found
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Validate exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get user's workouts
    workouts = db.query(Workout).filter(Workout.user_id == user_id).all()
    workout_ids = [w.id for w in workouts]
    
    if not workout_ids:
        return ExerciseProgress(
            exercise_id=exercise_id,
            exercise_name=exercise.name,
            total_sets=0,
            total_reps=0,
            max_weight_kg=0.0,
            avg_weight_kg=0.0,
            progression=[]
        )
    
    # Get workout logs
    logs = db.query(WorkoutLog).filter(
        WorkoutLog.workout_id.in_(workout_ids),
        WorkoutLog.performed_at >= start_date
    ).all()
    
    log_ids = [log.id for log in logs]
    
    if not log_ids:
        return ExerciseProgress(
            exercise_id=exercise_id,
            exercise_name=exercise.name,
            total_sets=0,
            total_reps=0,
            max_weight_kg=0.0,
            avg_weight_kg=0.0,
            progression=[]
        )
    
    # Get exercise sets
    sets = db.query(ExerciseSet, WorkoutLog).join(
        WorkoutLog, ExerciseSet.workout_log_id == WorkoutLog.id
    ).filter(
        ExerciseSet.workout_log_id.in_(log_ids),
        ExerciseSet.exercise_id == exercise_id
    ).order_by(WorkoutLog.performed_at).all()
    
    if not sets:
        return ExerciseProgress(
            exercise_id=exercise_id,
            exercise_name=exercise.name,
            total_sets=0,
            total_reps=0,
            max_weight_kg=0.0,
            avg_weight_kg=0.0,
            progression=[]
        )
    
    # Calculate stats
    weights = [float(s[0].weight_kg) for s in sets if s[0].weight_kg]
    total_sets = len(sets)
    total_reps = sum(s[0].reps or 0 for s in sets)
    max_weight = max(weights) if weights else 0.0
    avg_weight = sum(weights) / len(weights) if weights else 0.0
    
    # Build progression timeline
    progression = []
    for ex_set, log in sets:
        progression.append({
            "date": log.performed_at.isoformat(),
            "reps": ex_set.reps or 0,
            "weight_kg": float(ex_set.weight_kg) if ex_set.weight_kg else 0.0,
            "rpe": float(ex_set.rpe) if ex_set.rpe else None,
            "set_number": ex_set.set_number
        })
    
    return ExerciseProgress(
        exercise_id=exercise_id,
        exercise_name=exercise.name,
        total_sets=total_sets,
        total_reps=total_reps,
        max_weight_kg=round(max_weight, 2),
        avg_weight_kg=round(avg_weight, 2),
        progression=progression
    )
