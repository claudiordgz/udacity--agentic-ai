"""Tools for the Inventory Manager Agent."""

from smolagents import tool


@tool
def check_inventory() -> str:
    """
    Check current inventory levels of all ingredients.
    
    Returns:
        A summary of current inventory levels
    """
    from data.factory_state import factory_state
    inventory = factory_state.inventory
    
    items = []
    for item, amount in inventory.items():
        unit = "count" if item == "eggs" else "kg" if item != "water" else "liters"
        items.append(f"{item}: {amount} {unit}")
    
    return f"Current ingredients inventory: {', '.join(items)}"


@tool
def check_ingredients(pasta_shape: str, quantity: float) -> str:
    """
    Check if there are sufficient ingredients to fulfill an order.
    This is for CONFLICT DETECTION - prevents processing orders that can't be fulfilled.
    
    Args:
        pasta_shape: The type of pasta to produce
        quantity: Amount of pasta needed in kg
        
    Returns:
        A message indicating if ingredients are sufficient or not
    """
    from data.factory_state import factory_state
    
    # Get recipe for the pasta shape
    if pasta_shape in factory_state.pasta_recipes:
        recipe = factory_state.pasta_recipes[pasta_shape]
    elif pasta_shape in factory_state.custom_recipes:
        recipe = factory_state.custom_recipes[pasta_shape]
    else:
        return f"Recipe not found for {pasta_shape}"
    
    # Check each ingredient
    missing = []
    for ingredient, required_per_kg in recipe.items():
        total_required = required_per_kg * quantity
        available = factory_state.inventory.get(ingredient, 0)
        
        if available < total_required:
            shortfall = total_required - available
            missing.append(f"{ingredient} (need {total_required:.1f}, have {available:.1f})")
    
    if missing:
        missing_str = "; ".join(missing)
        return f"INSUFFICIENT ingredients for {quantity}kg of {pasta_shape}. Missing: {missing_str}"
    else:
        return f"SUFFICIENT ingredients for {quantity}kg of {pasta_shape}"


@tool
def check_pasta_recipe(pasta_shape: str) -> str:
    """
    Check what ingredients are needed for a specific pasta shape.
    
    Args:
        pasta_shape: The name of the pasta shape to check
        
    Returns:
        A message describing the recipe for the pasta shape
    """
    from data.factory_state import factory_state
    
    if pasta_shape in factory_state.pasta_recipes:
        recipe = factory_state.pasta_recipes[pasta_shape]
        ingredients_str = ", ".join([f"{k}: {v}" for k, v in recipe.items()])
        return f"{pasta_shape} recipe per kg: {ingredients_str}"
    elif pasta_shape in factory_state.custom_recipes:
        recipe = factory_state.custom_recipes[pasta_shape]
        ingredients_str = ", ".join([f"{k}: {v}" for k, v in recipe.items()])
        return f"Custom {pasta_shape} recipe per kg: {ingredients_str}"
    return f"Recipe not found for {pasta_shape}"
