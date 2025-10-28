"""Tools for the Order Processor Agent."""

from smolagents import tool


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
        return f"We make {pasta_shape}! Recipe per kg: {ingredients_str}"
    elif pasta_shape in factory_state.custom_recipes:
        recipe = factory_state.custom_recipes[pasta_shape]
        ingredients_str = ", ".join([f"{k}: {v}" for k, v in recipe.items()])
        return f"We make custom {pasta_shape}! Recipe per kg: {ingredients_str}"
    return f"Sorry, we don't currently make {pasta_shape}. Available shapes: {', '.join(factory_state.pasta_recipes.keys())}"


@tool
def generate_order_id() -> str:
    """
    Generate a unique order ID.
    
    Returns:
        A unique order ID in the format ORD-XXXX
    """
    from data.factory_state import factory_state
    factory_state.order_counter += 1
    return f"ORD-{factory_state.order_counter:04d}"

