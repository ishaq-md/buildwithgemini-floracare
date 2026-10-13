"""Watering schedule calculation tool for FloraCare."""

from typing import Any, Dict
from app.db import get_plant


def calculate_watering_schedule(
    plant_name: str,
    days_since_last_watered: int,
    light_condition: str = "medium indirect",
    pot_material: str = "plastic",
) -> Dict[str, Any]:
    """Calculates whether a plant needs watering based on species, care history, light, and pot material.

    Args:
        plant_name: Name of the houseplant (e.g. 'Monstera Deliciosa', 'Snake Plant', 'Peace Lily').
        days_since_last_watered: Number of days elapsed since the plant was last watered.
        light_condition: Environmental light level ('low', 'medium indirect', 'bright indirect', 'direct sun').
        pot_material: Pot material ('terracotta', 'plastic', 'glazed ceramic', 'nursery pot').

    Returns:
        A dictionary with watering status, days remaining, adjusted interval, and practical recommendations.
    """
    # 1. Fetch plant baseline from Firestore or use reasonable defaults
    plant = get_plant(plant_name)
    if "error" not in plant and "watering_interval_days" in plant:
        base_interval = int(plant["watering_interval_days"])
        resolved_name = plant.get("name", plant_name)
    else:
        base_interval = 7
        resolved_name = plant_name

    # 2. Adjust for light condition
    light_factor = 1.0
    light_lower = light_condition.lower()
    if "bright" in light_lower or "direct" in light_lower or "high" in light_lower:
        light_factor = 0.85
    elif "low" in light_lower:
        light_factor = 1.25

    # 3. Adjust for pot material
    pot_factor = 1.0
    pot_lower = pot_material.lower()
    if "terracotta" in pot_lower or "clay" in pot_lower:
        pot_factor = 0.85

    adjusted_interval = max(2, round(base_interval * light_factor * pot_factor))
    days_remaining = adjusted_interval - days_since_last_watered

    if days_remaining <= 0:
        status = "needs_water_now"
        recommendation = (
            f"Watering is due! It has been {days_since_last_watered} days since last watering "
            f"(adjusted cycle is every {adjusted_interval} days). Check if the top soil feels dry, then soak thoroughly."
        )
    elif days_remaining <= 2:
        status = "water_soon"
        recommendation = (
            f"Watering is due in {days_remaining} day(s). Feel the top 1-2 inches of soil with your finger; "
            "prepare to water soon if it feels dry."
        )
    else:
        status = "moisture_sufficient"
        recommendation = (
            f"No watering needed today. Next watering expected in approximately {days_remaining} day(s) "
            f"(cycle: every {adjusted_interval} days under {light_condition} light in a {pot_material} pot)."
        )

    return {
        "plant_name": resolved_name,
        "days_since_last_watered": days_since_last_watered,
        "base_interval_days": base_interval,
        "adjusted_interval_days": adjusted_interval,
        "days_remaining": days_remaining,
        "status": status,
        "recommendation": recommendation,
    }
