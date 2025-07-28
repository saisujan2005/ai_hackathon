pip install fastapi uvicorn pydantic openai

# main.py
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# ----- Data Models ----- #
class UserProfile(BaseModel):
    age: int
    weight: float
    height: float
    health_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []

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


# ----- Utility Functions ----- #
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)

def meal_plan_generator(profile, preferences, pantry):
    # Stub: Replace w/ GPT or recipe DB integration
    # For demo, just output a sample plan
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
    needed = set([i for meal in meals+snacks for i in meal.ingredients])
    owned = set([i.lower() for i in pantry.ingredients])
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
def simulate_blinkit(missing_ingredients: List[str] = Body(...)):
    # Simulate order creation
    return {
        "order_id": "BLK12345",
        "items": missing_ingredients,
        "status": "Simulated order placed"
    }

npx create-react-app diettly-frontend
cd diettly-frontend && npm start

import React, { useState } from "react";

function App() {
  const [profile, setProfile] = useState({
    age: 25, weight: 65, height: 170, health_conditions: [], allergies: []
  });
  const [preferences, setPreferences] = useState({
    diet_type: "Veg",
    cuisines: ["Indian"],
    fasting_mode: "",
  });
  const [pantry, setPantry] = useState({ ingredients: ["quinoa", "banana"] });
  const [mealPlan, setMealPlan] = useState();
  const [missing, setMissing] = useState([]);
  const [orderStatus, setOrderStatus] = useState();

  async function fetchMealPlan() {
    const res = await fetch("http://localhost:8000/mealplan", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        profile, preferences, pantry
      })
    });
    const data = await res.json();
    setMealPlan(data);
    setMissing(data.missing_ingredients);
  }

  async function orderMissing() {
    const res = await fetch("http://localhost:8000/blinkit/order", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(missing)
    });
    const data = await res.json();
    setOrderStatus(data.status);
  }

  return (
    <div style={{padding: 30}}>
      <h1>Diettly AI Agent Demo</h1>
      {/* ...add inputs here for changing profile/preferences/pantry... */}
      <button onClick={fetchMealPlan}>Generate Meal Plan</button>
      {mealPlan && (
        <div>
          <h2>Meals</h2>
          {mealPlan.meals.map(m => (
            <div key={m.name}>
              <b>{m.name}</b> - {m.macros.calories} kcal
              <br/>Ingredients: {m.ingredients.join(", ")}
              <br/>Instructions: {m.instructions}
              <hr/>
            </div>
          ))}
          <h3>Snacks</h3>
          {mealPlan.snacks.map(s => <div key={s.name}>{s.name}</div>)}
          <h3>Missing Ingredients: {missing.join(", ")}</h3>
          <button onClick={orderMissing} disabled={!missing.length}>
            Order Missing (Blinkit Sim)
          </button>
          <div>{orderStatus}</div>
        </div>
      )}
    </div>
  );
}

export default App;

# meal_llm.py
import openai

def get_meal_plan(prompt, api_key):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a nutrition expert who creates healthy meal plans."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message['content']

def generate_recipe(meal_description, api_key):
    prompt = f"Write a detailed, healthy recipe for: {meal_description}"
    return get_meal_plan(prompt, api_key)

def summarize_nutrition(recipe_text, api_key):
    prompt = f"Summarize the nutrition macros and calories line by line for this recipe:\n{recipe_text}"
    return get_meal_plan(prompt, api_key)

from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
def summarize_text(text):
    return summarizer(text, max_length=100, min_length=10, do_sample=False)[0]['summary_text']


# app.py
import streamlit as st
from meal_llm import get_meal_plan, generate_recipe, summarize_nutrition

st.set_page_config(page_title="AI Meal Planner", page_icon="🍽️", layout="centered")
st.title("Personalized AI Meal Planner 🍽️")

# Profile intake
with st.form("profile"):
    st.header("Profile")
    age = st.number_input("Age", min_value=13, max_value=90, step=1)
    weight = st.number_input("Weight (kg)")
    height = st.number_input("Height (cm)")
    conditions = st.text_input("Health Conditions (comma separated, e.g., PCOD, Diabetes)")
    allergies = st.text_input("Allergies/intolerances (comma separated)")
    submitted = st.form_submit_button("Save Profile")

# Preferences
st.header("Preferences")
diet = st.selectbox("Diet type", ["Vegetarian", "Vegan", "Keto", "No preference"])
cuisine = st.multiselect("Cuisine preference", ["Indian", "Mediterranean", "Italian", "Chinese", "Global"])
fasting = st.selectbox("Fasting mode", ["None", "Intermittent", "OMAD", "Custom"])

# Pantry
st.header("Your Pantry")
pantry_items = st.text_area("List your available ingredients (comma separated)")

# Generate Meal Plan
if st.button("Generate My Meal Plan"):
    prompt = f"""
    User Profile: Age {age}, Weight {weight}kg, Height {height}cm, Conditions: {conditions}, Allergies: {allergies}.
    Preferences: Diet {diet}, Cuisines {', '.join(cuisine)}, Fasting: {fasting}.
    Pantry: {pantry_items}.

    Generate 3 meals + 2 snacks. Each meal must fit health and allergen restrictions, use pantry, and respect preferences.
    Provide a summary (dish name, brief description, macros).
    """
    # Replace with your own OpenAI key/secure storage in production
    api_key = "YOUR_OPENAI_KEY"
    meal_plan = get_meal_plan(prompt, api_key)
    st.markdown(meal_plan)
    st.success("Meal plan generated!")

# Select Meal for Recipe & Macro Breakdown
selected_meal = st.text_input("Copy-paste a meal name from above to get full recipe")
if selected_meal:
    api_key = "YOUR_OPENAI_KEY"
    recipe = generate_recipe(selected_meal, api_key)
    st.subheader("Recipe")
    st.markdown(recipe)

    nutrition = summarize_nutrition(recipe, api_key)
    st.subheader("Nutrition Info")
    st.markdown(nutrition)


