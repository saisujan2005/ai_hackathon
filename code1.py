from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# --- Enable CORS for localhost frontend development ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Data Models ----- #
class UserProfile(BaseModel):
    age: int
    weight: float
    height: float
    health_conditions: Optional[List[str]] = Field(default_factory=list)
    allergies: Optional[List[str]] = Field(default_factory=list)

class Preferences(BaseModel):
    diet_type: str
    cuisines: List[str]
    fasting_mode: Optional[str] = None

class Pantry(BaseModel):
    ingredients: List[str]

class MealPlanRequest(BaseModel):
    profile: UserProfile
    preferences: Preferences
    pantry: Pantry

class Meal(BaseModel):
    name: str
    ingredients: List[str]
    instructions: str
    macros: dict

class MealPlanResponse(BaseModel):
    meals: List[Meal]
    snacks: List[Meal]
    missing_ingredients: List[str]

class BlinkitOrderRequest(BaseModel):
    missing_ingredients: List[str]


# ----- Utility Functions ----- #
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)

def meal_plan_generator(profile, preferences, pantry):
    # Stub: Replace with GPT or recipe DB in real world
    meals = [
        Meal(
            name="Quinoa Salad",
            ingredients=["quinoa", "cherry tomatoes", "cucumber", "olive oil"],
            instructions="Cook quinoa, mix with veggies, dress with olive oil.",
            macros={"calories": 400, "protein": 10, "carbs": 60, "fat": 15}
        )
    ]
    snacks = [
        Meal(
            name="Fruit Bowl",
            ingredients=["apple", "banana"],
            instructions="Chop fruits, mix and serve.",
            macros={"calories": 150, "protein": 1, "carbs": 35, "fat": 1}
        )
    ]
    # Ingredient gap analysis
    needed = set(i.lower() for meal in meals + snacks for i in meal.ingredients)
    owned = set(i.lower() for i in pantry.ingredients)
    missing = list(needed - owned)
    return MealPlanResponse(meals=meals, snacks=snacks, missing_ingredients=missing)

# ----- API Endpoints ----- #
@app.post("/profile/bmi")
def get_bmi(profile: UserProfile):
    bmi = calculate_bmi(profile.weight, profile.height)
    return {"bmi": bmi}

@app.post("/mealplan")
def generate_mealplan(req: MealPlanRequest):
    return meal_plan_generator(req.profile, req.preferences, req.pantry)

@app.post("/blinkit/order")
def simulate_blinkit(req: BlinkitOrderRequest):
    return {
        "order_id": "BLK12345",
        "items": req.missing_ingredients,
        "status": "Simulated order placed"
    }



