import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("FOODOSCOPE_API_KEY")
# CONFIGURATION

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'User-Agent': 'PostmanRuntime/7.51.1'
}

BASE_API = "http://cosylab.iiitd.edu.in:6969"

# Load ingredient DB once (efficient)
with open("ingredients_molecules.json", "r") as f:
    INGREDIENT_DATA = json.load(f)

# RECIPE FUNCTIONS

def getRecipeInfo(user_input):
    print(f"\nNEURO-SCAN: {user_input.upper()}")

    url = f"{BASE_API}/recipe2-api/recipe-bytitle/recipeByTitle?title={user_input}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print("Error fetching recipe.")
        return None

    data = response.json()

    if not data.get("data"):
        print("No recipe found.")
        return None

    recipe = data["data"][0]

    print(f"Recipe Name: {recipe['Recipe_title']}")
    print(f"Calories: {recipe['Calories']}")
    print(f"Region: {recipe['Region']}")
    print(f"Continent: {recipe['Continent']}")

    return recipe["Recipe_id"]

def normalize(ingredient):
    ingredient = ingredient.lower().strip()

    if ingredient.endswith("oes"):
        return ingredient[:-2]      
    elif ingredient.endswith("ies"):
        return ingredient[:-3] + "y"  
    elif ingredient.endswith("es"):
        return ingredient[:-2]
    elif ingredient.endswith("s") and not ingredient.endswith("ss"):
        return ingredient[:-1]

    return ingredient

def getIngredientsForRecipe(recipe_id):
    url = f"{BASE_API}/recipe2-api/search-recipe/{recipe_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return []

    data = response.json()
    raw = [item["ingredient"] for item in data.get("ingredients", [])]
    return [normalize(i) for i in raw]


def searchRecipeByIngredient(ingredient):

    ingredient = normalize(ingredient)  

    url = f"{BASE_API}/recipe2-api/recipebyingredient/by-ingredients-categories-title"

    params = {
        "includeIngredients": ingredient,
        "page": 1,
        "limit": 20
    }

    response = requests.get(url, headers=HEADERS, params=params)

    print("URL:", response.url)
    print("Status:", response.status_code)

    if response.status_code != 200:
        print("Error:", response.text)
        return []

    data = response.json()

    return data.get("payload", {}).get("data", [])

# MOLECULE LOGIC

HEALTH_SCORE = {

    # Grains
    "wheat": 6,
    "whole wheat": 9,
    "white bread": 3,
    "brown rice": 9,
    "white rice": 5,
    "quinoa": 10,
    "oats": 10,
    "barley": 9,
    "millet": 9,
    "corn": 6,
    "maida": 2,

    # Vegetables
    "spinach": 10,
    "kale": 10,
    "broccoli": 10,
    "carrot": 9,
    "tomato": 8,
    "onion": 7,
    "garlic": 9,
    "capsicum": 8,
    "bell pepper": 8,
    "cabbage": 8,
    "cauliflower": 9,
    "peas": 8,
    "potato": 5,
    "sweet potato": 9,
    "beetroot": 9,
    "lettuce": 8,
    "cucumber": 8,
    "zucchini": 8,
    "mushroom": 9,
    "green beans": 8,
    "eggplant": 8,

    # Fruits
    "apple": 9,
    "banana": 8,
    "orange": 9,
    "mango": 7,
    "pineapple": 8,
    "strawberry": 9,
    "blueberry": 10,
    "papaya": 9,
    "grapes": 8,
    "watermelon": 8,
    "pear": 9,
    "pomegranate": 10,
    "kiwi": 9,

    # Proteins
    "chicken": 8,
    "grilled chicken": 9,
    "fried chicken": 3,
    "mutton": 5,
    "beef": 5,
    "fish": 9,
    "salmon": 10,
    "tuna": 9,
    "egg": 9,
    "tofu": 10,
    "paneer": 6,
    "lentils": 10,
    "chickpeas": 9,
    "rajma": 9,
    "soybeans": 10,
    "black beans": 9,

    # Nuts & Seeds
    "almonds": 10,
    "walnuts": 10,
    "cashews": 7,
    "peanuts": 8,
    "chia seeds": 10,
    "flax seeds": 10,
    "pumpkin seeds": 9,
    "sunflower seeds": 9,

    # Fats & Oils
    "olive oil": 10,
    "mustard oil": 8,
    "coconut oil": 7,
    "butter": 4,
    "ghee": 6,
    "vegetable oil": 4,
    "margarine": 2,

    # Additives / Less Healthy
    "sugar": 1,
    "brown sugar": 3,
    "jaggery": 6,
    "honey": 7,
    "salt": 3,
    "mayonnaise": 2,
    "cream": 4,
    "cheese": 5,
    "processed cheese": 2,
    "ketchup": 3,
    "soy sauce": 4,

    # Processed / Junk
    "white pasta": 3,
    "whole wheat pasta": 8,
    "burger bun": 3,
    "whole wheat bun": 8,
    "noodles": 4,
    "instant noodles": 1,
    "pizza base": 3,
    "brown bread": 7,
    "shrimp": 8,
    "ginger": 9,
    "ginger root": 9,
    "stock": 5,
    "chicken stock": 5,
    "shrimp stock": 6,
    "pepper": 7,
    "black pepper": 7,
}

def calculateHealthScore(ingredients):
    score = 0

    if isinstance(ingredients, str):
        ingredients = [ingredients]

    for ingredient in ingredients:
        ingredient = ingredient.lower().strip()

        # Exact match
        if ingredient in HEALTH_SCORE:
            score += HEALTH_SCORE[ingredient]
            continue

        # Smarter partial match
        for key in HEALTH_SCORE:
            if key in ingredient or ingredient in key:
                score += HEALTH_SCORE[key]
                break

    return score


def findHealthierIngredientsWithSameMolecules(base):

    base = base.lower().strip()

    # Try exact match first
    if base in INGREDIENT_DATA:
        base_key = base
    else:
        # Try partial match
        base_key = None
        for key in INGREDIENT_DATA:
            if key in base or base in key:
                base_key = key
                break

        if not base_key:
            return []

    base_molecules = set(INGREDIENT_DATA[base_key])
    base_score = calculateHealthScore([base_key])

    healthier = []

    for ingredient, molecules in INGREDIENT_DATA.items():

        if ingredient == base_key:
            continue

        shared = base_molecules.intersection(set(molecules))

        if len(shared) >= 3:   # require meaningful similarity
            new_score = calculateHealthScore(ingredient)

            if new_score > base_score:
                healthier.append({
                    "replacement": ingredient,
                    "shared_molecules": list(shared),
                    "score_gain": new_score - base_score
                })

    healthier.sort(key=lambda x: x["score_gain"], reverse=True)

    return healthier[:5]


# FLAVOR VALIDATION

def validateFlavorPairing(original, replacement):
    original = original.lower().strip()
    replacement = replacement.lower().strip()

    url = f"{BASE_API}/flavour-api/flavor-pairing-by-ingredient/{original}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return False

    data = response.json()

    if "data" not in data:
        return False

    paired = [
        item.get("entity_alias_readable", "").lower()
        for item in data["data"]
    ]

    return replacement in paired


def getValidatedHealthyReplacements(ingredients):

    validated = {}

    for ingredient in ingredients:

        ingredient = ingredient.lower().strip()

        # Skip already healthy ingredients
        base_score = calculateHealthScore([ingredient])
        if base_score >= 8:
            continue

        # Find molecule-based healthier options
        healthier_options = findHealthierIngredientsWithSameMolecules(ingredient)

        if not healthier_options:
            continue

        valid_options = []
        seen_replacements = set()

        for option in healthier_options:

            replacement = option["replacement"].lower().strip()

            # Avoid duplicates
            if replacement in seen_replacements:
                continue

            # Validate flavor pairing (fail-safe)
            try:
                is_valid = validateFlavorPairing(ingredient, replacement)
            except:
                is_valid = False

            if is_valid:
                valid_options.append(option)
                seen_replacements.add(replacement)

            # Limit to top 3 strong replacements
            if len(valid_options) == 3:
                break

        if valid_options:
            validated[ingredient] = valid_options

    return validated


# RECIPE REBUILD

def generateUpgradedIngredientList(original, validated_dict):

    upgraded = []

    for ing in original:

        if ing in validated_dict:
            upgraded.append(validated_dict[ing][0]["replacement"])
        else:
            upgraded.append(ing)

    return upgraded

def filterHealthyRecipes(recipes):

    healthy = []

    for r in recipes:
        try:
            if (
                float(r.get("vegan", 0)) == 1.0
                or float(r.get("pescetarian", 0)) == 1.0
                or float(r.get("lacto_vegetarian", 0)) == 1.0
                or float(r.get("ovo_lacto_vegetarian", 0)) == 1.0
            ):
                healthy.append(r)
        except:
            continue

    return healthy

# SMART INGREDIENT SELECTION

PROTEINS = [
    "chicken", "fish", "salmon", "tuna", "shrimp",
    "egg", "tofu", "paneer", "beef", "mutton"
]

GRAINS = [
    "rice", "brown rice", "white rice",
    "pasta", "vermicelli", "noodles",
    "quinoa", "oats", "barley", "millet", "wheat"
]

VEGETABLES = [
    "tomato", "onion", "garlic", "spinach",
    "broccoli", "carrot", "cabbage",
    "capsicum", "bell pepper", "peas"
]


def selectCoreIngredients(ingredients):
    # BROADENED LOGIC: Only pick 2 ingredients to increase search matches
    selected = []
    
    # Try to find one protein and one vegetable
    for ing in ingredients:
        if any(p in ing.lower() for p in PROTEINS) and not selected:
            selected.append(ing)
            break
            
    for ing in ingredients:
        if any(v in ing.lower() for v in VEGETABLES) and len(selected) < 2:
            if ing not in selected:
                selected.append(ing)
                break
                
    # Fallback: if we still don't have 2, just grab the first available
    if len(selected) < 2 and ingredients:
        for ing in ingredients:
            if ing not in selected:
                selected.append(ing)
                if len(selected) == 2: break
                
    return selected

def findRecipesFromIngredients(ingredients, original_calories):

    # Select only core ingredients
    core = selectCoreIngredients(ingredients)

    ingredient_query = ",".join(core)

    url = f"{BASE_API}/recipe2-api/recipebyingredient/by-ingredients-categories-title"

    params = {
        "includeIngredients": ingredient_query,
        "page": 1,
        "limit": 20
    }

    print("\nSearching with core ingredients:", core)

    response = requests.get(url, headers=HEADERS, params=params)

    print("URL:", response.url)
    print("Status:", response.status_code)

    if response.status_code != 200:
        return []

    data = response.json()
    recipes = data.get("payload", {}).get("data", [])

    healthy_recipes = []

    for r in recipes:
        try:
            if float(r["Calories"]) < float(original_calories):
                healthy_recipes.append(r)
        except:
            continue

    print("Lower calorie recipes:", len(healthy_recipes))

    return healthy_recipes

def getFullRecipeDetails(recipe_id):

    url = f"{BASE_API}/recipe2-api/search-recipe/{recipe_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return None

    data = response.json()

    instructions = data.get("instructions", [])

    if isinstance(instructions, str):
        instructions = [instructions]

    return {
        "ingredients": [item["ingredient"] for item in data.get("ingredients", [])],
        "instructions": instructions,
        "nutrition": data.get("nutrition", {})
    }

# MASTER FUNCTION 

# ... (Keep all existing code above the upgradeRecipe function exactly as is)

# ... (Keep all code from imports down to getFullRecipeDetails)

# ... (keep all your existing imports and helper functions above)

# ... [Keep all your helper functions like calculateHealthScore, etc.] ...

# In main.py
# In main.py
def upgradeRecipe(recipe_name):

    recipe_id = getRecipeInfo(recipe_name)
    if not recipe_id:
        return []

    original_ingredients = getIngredientsForRecipe(recipe_id)

    # Fetch original recipe info
    url = f"{BASE_API}/recipe2-api/recipe-bytitle/recipeByTitle?title={recipe_name}"
    response = requests.get(url, headers=HEADERS)
    original_data = response.json().get("data", [{}])[0]

    original_calories = float(original_data.get("Calories", 500))
    original_continent = original_data.get("Continent", "")
    original_region = original_data.get("Region", "")

    validated = getValidatedHealthyReplacements(original_ingredients)
    upgraded = generateUpgradedIngredientList(original_ingredients, validated)

    recipes = findRecipesFromIngredients(upgraded, original_calories)

    results = []

    for r in recipes:
        rid = r["Recipe_id"]
        details = getFullRecipeDetails(rid)
        if not details:
            continue

        ingredients = getIngredientsForRecipe(rid)
        health_score = calculateHealthScore(ingredients)

        results.append({
            "title": r.get("Recipe_title"),
            "calories": float(r.get("Calories", 0)),
            "region": r.get("Region"),
            "continent": r.get("Continent"),
            "health_score": health_score,
            "ingredients": details["ingredients"],
        })

    # Smart ranking: highest health score first, then lowest calories
    results.sort(
        key=lambda x: (-x["health_score"], x["calories"])
    )

    return results[:3]


# Remove the 'craving = input(...)' and 'upgradeRecipe(craving)' lines 
# at the bottom so they don't block the Flask server.