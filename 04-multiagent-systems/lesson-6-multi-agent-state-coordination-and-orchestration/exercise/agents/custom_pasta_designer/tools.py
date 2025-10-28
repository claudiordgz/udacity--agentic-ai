"""Tools for the Custom Pasta Designer Agent."""

from smolagents import tool


@tool
def check_inventory() -> str:
    """Check current inventory levels of all ingredients."""
    from data.factory_state import factory_state
    inventory = factory_state.inventory
    
    items = []
    for item, amount in inventory.items():
        unit = "count" if item == "eggs" else "kg" if item != "water" else "liters"
        items.append(f"{item}: {amount} {unit}")
    
    return f"Available ingredients: {', '.join(items)}"


@tool
def create_custom_pasta_recipe(pasta_name: str, ingredients: dict) -> str:
    """
    Create a custom pasta recipe with specific ingredient ratios.
    
    Args:
        pasta_name: Name of the custom pasta
        ingredients: Dictionary mapping ingredient names to amounts needed per kg
        
    Returns:
        Status of the recipe creation
    """
    from data.factory_state import factory_state
    
    # Validate ingredients exist in inventory
    for ingredient in ingredients.keys():
        if ingredient not in factory_state.inventory:
            return f"Error: Ingredient '{ingredient}' is not available in our inventory."
    
    # Add the custom recipe
    factory_state.custom_recipes[pasta_name] = ingredients
    
    ingredients_str = ", ".join([f"{k}: {v}" for k, v in ingredients.items()])
    return f"Custom recipe '{pasta_name}' created successfully! Recipe per kg: {ingredients_str}"


@tool
def check_existing_recipes() -> str:
    """Check what standard and custom pasta recipes are available."""
    from data.factory_state import factory_state
    
    standard = ", ".join(factory_state.pasta_recipes.keys())
    custom = ", ".join(factory_state.custom_recipes.keys()) if factory_state.custom_recipes else "None"
    
    return f"Standard recipes: {standard}. Custom recipes: {custom}"

