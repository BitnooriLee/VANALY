from pydantic import BaseModel, Field
from typing import Literal


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(default="코치님", max_length=50)


class UserResponse(BaseModel):
    id: int
    name: str
    created_at: str


# ── Goals ─────────────────────────────────────────────────────────────────────

GoalType = Literal["weight_loss", "maintenance", "muscle_gain"]


class GoalsUpdate(BaseModel):
    daily_calories: int = Field(default=2000, ge=800, le=5000)
    carbs_pct: float = Field(default=50.0, ge=10.0, le=80.0)
    protein_pct: float = Field(default=25.0, ge=10.0, le=60.0)
    fat_pct: float = Field(default=25.0, ge=10.0, le=60.0)
    goal_type: GoalType = "maintenance"


class GoalsResponse(GoalsUpdate):
    user_id: int
    updated_at: str


# ── Meal ──────────────────────────────────────────────────────────────────────

BloodSugarImpact = Literal["low", "medium", "high"]


class MealAnalysisResponse(BaseModel):
    id: int
    user_id: int
    food_items: list[str]
    calories: int
    carbs_g: float
    protein_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float
    glycemic_load: float
    blood_sugar_impact: BloodSugarImpact
    energy_peak_minutes: int
    confidence: float
    feedback_text: str
    next_meal_suggestion: str
    eaten_at: str


class MealListResponse(BaseModel):
    meals: list[MealAnalysisResponse]
    total: int


# ── Error ─────────────────────────────────────────────────────────────────────

class AnalysisError(BaseModel):
    error: Literal["not_food", "unclear", "api_error"]
    message: str
