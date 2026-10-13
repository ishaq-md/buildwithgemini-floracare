"""Firestore database service and tools for FloraCare."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Hardcoded project ID as required to prevent issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-bccd001ca2e2"
COLLECTION_NAME = "plants"


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client configured with the hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_plants(limit: int = 10) -> List[Dict[str, Any]]:
    """Lists houseplants currently available in the FloraCare catalog.

    Args:
        limit: Maximum number of plants to return (default 10).

    Returns:
        A list of plant records including name, difficulty, light, watering, and price.
    """
    db = get_firestore_client()
    plants_ref = db.collection(COLLECTION_NAME).limit(limit)
    docs = plants_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_plant(plant_name_or_id: str) -> Dict[str, Any]:
    """Retrieves detailed information for a specific houseplant by name or ID.

    Args:
        plant_name_or_id: The name or slug ID of the plant (e.g., 'Monstera Deliciosa' or 'monstera-deliciosa').

    Returns:
        The plant document data including care guide, watering schedule, and stock, or an error dictionary.
    """
    db = get_firestore_client()
    coll = db.collection(COLLECTION_NAME)

    # 1. Try direct document ID lookup
    slug = plant_name_or_id.strip().lower().replace(" ", "-").replace("(", "").replace(")", "")
    doc = coll.document(slug).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # 2. Try case-insensitive matching across collection
    for d in coll.stream():
        data = d.to_dict()
        name = data.get("name", "").lower()
        scientific = data.get("scientific_name", "").lower()
        query_clean = plant_name_or_id.strip().lower()
        if query_clean in name or query_clean in scientific or name in query_clean:
            data["id"] = d.id
            return data

    return {"error": f"Plant '{plant_name_or_id}' not found in catalog."}


def search_plants_by_care(care_difficulty: str = "", light_preference: str = "") -> List[Dict[str, Any]]:
    """Searches and filters plants by care difficulty and/or light requirements.

    Args:
        care_difficulty: Optional difficulty filter (e.g. 'Easy', 'Very Easy', 'Moderate').
        light_preference: Optional light filter (e.g. 'Low', 'Indirect', 'Bright').

    Returns:
        A list of matching plant records.
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()

    results = []
    diff_lower = care_difficulty.strip().lower()
    light_lower = light_preference.strip().lower()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        diff_match = (not diff_lower) or (diff_lower in data.get("care_difficulty", "").lower())
        light_match = (not light_lower) or (light_lower in data.get("light_requirements", "").lower())
        if diff_match and light_match:
            results.append(data)

    return results


def add_plant_to_catalog(
    name: str,
    scientific_name: str,
    care_difficulty: str,
    light_requirements: str,
    watering_frequency: str,
    watering_interval_days: int,
    description: str,
    price: float,
    in_stock: int,
) -> Dict[str, Any]:
    """Adds a new houseplant to the Firestore catalog.

    Args:
        name: Common name of the plant (e.g. 'ZZ Plant').
        scientific_name: Scientific botanical name (e.g. 'Zamioculcas zamiifolia').
        care_difficulty: Difficulty level (e.g. 'Easy', 'Moderate', 'Expert').
        light_requirements: Light conditions needed (e.g. 'Low to bright indirect light').
        watering_frequency: Description of watering schedule (e.g. 'Every 2-3 weeks').
        watering_interval_days: Typical interval between waterings in days (e.g. 14).
        description: Brief description and care notes.
        price: Retail price in USD (e.g. 28.50).
        in_stock: Initial inventory count (e.g. 15).

    Returns:
        A dictionary confirming addition and returning the created document details.
    """
    db = get_firestore_client()
    doc_id = name.strip().lower().replace(" ", "-").replace("(", "").replace(")", "")
    plant_data = {
        "name": name.strip(),
        "scientific_name": scientific_name.strip(),
        "care_difficulty": care_difficulty.strip(),
        "light_requirements": light_requirements.strip(),
        "watering_frequency": watering_frequency.strip(),
        "watering_interval_days": int(watering_interval_days),
        "description": description.strip(),
        "price": float(price),
        "in_stock": int(in_stock),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection(COLLECTION_NAME).document(doc_id).set(plant_data)
    plant_data["id"] = doc_id
    return {"status": "success", "message": f"Added '{name}' to catalog.", "plant": plant_data}


def log_plant_care_event(plant_name_or_id: str, action: str, notes: str = "") -> Dict[str, Any]:
    """Logs a care event (such as watering, fertilizing, repotting) for a plant in Firestore.

    Args:
        plant_name_or_id: The name or ID of the plant.
        action: The care action taken (e.g. 'Watered', 'Fertilized', 'Repotted', 'Pruned').
        notes: Any observations or notes (e.g. 'Soil was dry, watered thoroughly').

    Returns:
        A dictionary confirming the care event was logged.
    """
    plant = get_plant(plant_name_or_id)
    if "error" in plant:
        return plant

    db = get_firestore_client()
    doc_id = plant["id"]
    timestamp = datetime.now(timezone.utc).isoformat()
    care_entry = {
        "action": action,
        "notes": notes,
        "timestamp": timestamp,
    }

    # Record the care log under a subcollection 'care_history'
    db.collection(COLLECTION_NAME).document(doc_id).collection("care_history").add(care_entry)

    # Also update the plant document's last_cared field
    db.collection(COLLECTION_NAME).document(doc_id).update({
        f"last_{action.lower()}": timestamp,
        "updated_at": timestamp,
    })

    return {
        "status": "success",
        "message": f"Successfully logged '{action}' for {plant.get('name')}.",
        "care_entry": care_entry,
    }
