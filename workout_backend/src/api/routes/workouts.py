from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID

from src.database.connection import get_db
from src.models import Workout, WorkoutExercise, Exercise, Equipment, User, WorkoutLog
from pydantic import BaseModel, Field

router = APIRouter(prefix="/workouts", tags=["workouts"])


class WorkoutGenerateRequest(BaseModel):
    """Request schema for generating a workout."""
    user_id: UUID = Field(..., description="User ID for whom to generate the workout")
    goal: str = Field(..., description="Workout goal: 'strength', 'hypertrophy', 'endurance', 'weight_loss', or 'general'")
    equipment: Optional[List[str]] = Field(None, description="List of available equipment names (e.g., ['Barbell', 'Dumbbell'])")
    duration_minutes: Optional[int] = Field(45, description="Target workout duration in minutes")


class WorkoutGenerateResponse(BaseModel):
    """Response schema for generated workout."""
    workout_id: UUID = Field(..., description="Unique identifier for the generated workout")
    goal: str = Field(..., description="Workout goal")
    exercises: List[dict] = Field(..., description="List of exercises with details")
    estimated_duration: int = Field(..., description="Estimated workout duration in minutes")


class CustomWorkoutRequest(BaseModel):
    """Request schema for creating a custom workout."""
    user_id: UUID = Field(..., description="User ID who owns the workout")
    goal: str = Field(..., description="Workout goal")
    exercises: List[dict] = Field(..., description="List of exercises with exercise_id, target_sets, target_reps, rest_seconds")


# PUBLIC_INTERFACE
@router.post("/generate", 
             response_model=WorkoutGenerateResponse,
             summary="Generate a personalized workout",
             description="Generate a workout plan based on user goals, available equipment, and duration preferences")
async def generate_workout(
    request: WorkoutGenerateRequest,
    db: Session = Depends(get_db)
) -> WorkoutGenerateResponse:
    """
    Generate a personalized workout plan.
    
    This endpoint creates an intelligent workout based on:
    - User's fitness goal (strength, hypertrophy, endurance, weight loss, general)
    - Available equipment
    - Target duration
    
    The algorithm selects exercises targeting different muscle groups to ensure
    a balanced workout session.
    
    Args:
        request: Workout generation parameters
        db: Database session
        
    Returns:
        WorkoutGenerateResponse: Generated workout with exercises and details
        
    Raises:
        HTTPException: 404 if user not found, 400 if invalid parameters
    """
    # Validate user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {request.user_id} not found"
        )
    
    # Validate goal
    valid_goals = ["strength", "hypertrophy", "endurance", "weight_loss", "general"]
    goal = request.goal.lower()
    if goal not in valid_goals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid goal. Must be one of: {', '.join(valid_goals)}"
        )
    
    # Build exercise query based on equipment availability
    exercise_query = db.query(Exercise)
    
    if request.equipment:
        # Get equipment IDs for the requested equipment
        equipment_ids = db.query(Equipment.id).filter(
            Equipment.name.in_(request.equipment)
        ).all()
        equipment_ids = [eq[0] for eq in equipment_ids]
        
        # Filter exercises by equipment (include bodyweight exercises too)
        exercise_query = exercise_query.filter(
            (Exercise.equipment_id.in_(equipment_ids)) | 
            (Exercise.equipment_id.is_(None))
        )
    
    # Get exercises grouped by muscle groups
    exercises = exercise_query.all()
    
    if not exercises:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No exercises found matching the equipment criteria"
        )
    
    # Group exercises by primary muscle
    muscle_groups = {}
    for exercise in exercises:
        muscle = exercise.primary_muscle or "general"
        if muscle not in muscle_groups:
            muscle_groups[muscle] = []
        muscle_groups[muscle].append(exercise)
    
    # Select exercises based on goal
    selected_exercises = []
    
    # Define sets/reps based on goal
    if goal == "strength":
        target_sets, target_reps = 5, 5
        rest_seconds = 180
    elif goal == "hypertrophy":
        target_sets, target_reps = 4, 10
        rest_seconds = 90
    elif goal == "endurance":
        target_sets, target_reps = 3, 15
        rest_seconds = 60
    elif goal == "weight_loss":
        target_sets, target_reps = 3, 12
        rest_seconds = 45
    else:  # general
        target_sets, target_reps = 3, 10
        rest_seconds = 90
    
    # Select 1-2 exercises per major muscle group
    major_groups = ["chest", "back", "legs", "shoulders", "arms"]
    exercises_per_group = 1 if len(muscle_groups) > 5 else 2
    
    for muscle in major_groups:
        if muscle in muscle_groups:
            import random
            selected = random.sample(
                muscle_groups[muscle],
                min(exercises_per_group, len(muscle_groups[muscle]))
            )
            selected_exercises.extend(selected)
    
    # If we still need more exercises to fill duration, add from other groups
    target_exercise_count = max(5, request.duration_minutes // 10)
    if len(selected_exercises) < target_exercise_count:
        remaining_exercises = [ex for ex in exercises if ex not in selected_exercises]
        if remaining_exercises:
            import random
            additional = random.sample(
                remaining_exercises,
                min(target_exercise_count - len(selected_exercises), len(remaining_exercises))
            )
            selected_exercises.extend(additional)
    
    # Create workout
    workout = Workout(
        user_id=request.user_id,
        goal=goal
    )
    db.add(workout)
    db.flush()  # Get the workout ID
    
    # Add exercises to workout
    exercise_details = []
    for exercise in selected_exercises:
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=exercise.id,
            target_sets=target_sets,
            target_reps=target_reps,
            rest_seconds=rest_seconds
        )
        db.add(workout_exercise)
        
        exercise_details.append({
            "exercise_id": exercise.id,
            "exercise_name": exercise.name,
            "primary_muscle": exercise.primary_muscle,
            "target_sets": target_sets,
            "target_reps": target_reps,
            "rest_seconds": rest_seconds
        })
    
    db.commit()
    db.refresh(workout)
    
    # Calculate estimated duration
    estimated_duration = len(selected_exercises) * target_sets * (target_reps * 3 + rest_seconds) // 60
    
    return WorkoutGenerateResponse(
        workout_id=workout.id,
        goal=goal,
        exercises=exercise_details,
        estimated_duration=estimated_duration
    )


# PUBLIC_INTERFACE
@router.post("/custom",
             response_model=WorkoutGenerateResponse,
             summary="Create a custom workout",
             description="Create a custom workout with user-selected exercises")
async def create_custom_workout(
    request: CustomWorkoutRequest,
    db: Session = Depends(get_db)
) -> WorkoutGenerateResponse:
    """
    Create a custom workout with user-selected exercises.
    
    Args:
        request: Custom workout parameters
        db: Database session
        
    Returns:
        WorkoutGenerateResponse: Created workout with exercises
        
    Raises:
        HTTPException: 404 if user or exercises not found, 400 if invalid parameters
    """
    # Validate user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {request.user_id} not found"
        )
    
    if not request.exercises:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one exercise must be provided"
        )
    
    # Validate all exercises exist
    exercise_ids = [ex.get("exercise_id") for ex in request.exercises]
    exercises = db.query(Exercise).filter(Exercise.id.in_(exercise_ids)).all()
    
    if len(exercises) != len(exercise_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more exercises not found"
        )
    
    # Create workout
    workout = Workout(
        user_id=request.user_id,
        goal=request.goal
    )
    db.add(workout)
    db.flush()
    
    # Add exercises to workout
    exercise_details = []
    exercises_dict = {ex.id: ex for ex in exercises}
    
    for ex_data in request.exercises:
        exercise = exercises_dict[ex_data["exercise_id"]]
        
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=ex_data["exercise_id"],
            target_sets=ex_data.get("target_sets", 3),
            target_reps=ex_data.get("target_reps", 10),
            rest_seconds=ex_data.get("rest_seconds", 90)
        )
        db.add(workout_exercise)
        
        exercise_details.append({
            "exercise_id": exercise.id,
            "exercise_name": exercise.name,
            "primary_muscle": exercise.primary_muscle,
            "target_sets": workout_exercise.target_sets,
            "target_reps": workout_exercise.target_reps,
            "rest_seconds": workout_exercise.rest_seconds
        })
    
    db.commit()
    db.refresh(workout)
    
    # Calculate estimated duration
    estimated_duration = sum(
        ex["target_sets"] * (ex["target_reps"] * 3 + ex["rest_seconds"]) 
        for ex in exercise_details
    ) // 60
    
    return WorkoutGenerateResponse(
        workout_id=workout.id,
        goal=request.goal,
        exercises=exercise_details,
        estimated_duration=estimated_duration
    )


# PUBLIC_INTERFACE
@router.get("/history",
            response_model=List[dict],
            summary="Get workout history",
            description="Retrieve workout history for a user with logged sessions")
async def get_workout_history(
    user_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get workout history for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of workouts to return
        db: Database session
        
    Returns:
        List of workouts with log information
        
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
    
    # Get workouts with their logs
    workouts = db.query(Workout).filter(
        Workout.user_id == user_id
    ).order_by(desc(Workout.created_at)).limit(limit).all()
    
    history = []
    for workout in workouts:
        # Get workout exercises
        workout_exercises = db.query(WorkoutExercise, Exercise).join(
            Exercise, WorkoutExercise.exercise_id == Exercise.id
        ).filter(WorkoutExercise.workout_id == workout.id).all()
        
        # Get logs for this workout
        logs = db.query(WorkoutLog).filter(
            WorkoutLog.workout_id == workout.id
        ).order_by(desc(WorkoutLog.performed_at)).all()
        
        history.append({
            "workout_id": workout.id,
            "goal": workout.goal,
            "created_at": workout.created_at,
            "exercise_count": len(workout_exercises),
            "exercises": [
                {
                    "exercise_id": ex.id,
                    "exercise_name": exercise.name,
                    "target_sets": ex.target_sets,
                    "target_reps": ex.target_reps
                }
                for ex, exercise in workout_exercises
            ],
            "logs": [
                {
                    "log_id": log.id,
                    "performed_at": log.performed_at,
                    "duration_minutes": log.duration_minutes
                }
                for log in logs
            ],
            "times_completed": len(logs)
        })
    
    return history
