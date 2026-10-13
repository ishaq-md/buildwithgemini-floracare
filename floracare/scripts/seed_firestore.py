#!/usr/bin/env python3
"""Seed Firestore database with initial plants catalog for FloraCare."""

from google.cloud import firestore

# Hardcoded project ID as required to prevent issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-bccd001ca2e2"
COLLECTION_NAME = "plants"

SAMPLE_PLANTS = [
    {
        "name": "Monstera Deliciosa",
        "scientific_name": "Monstera deliciosa",
        "care_difficulty": "Easy",
        "light_requirements": "Medium to bright indirect light",
        "watering_frequency": "Water every 1-2 weeks; allow top 2-3 inches of soil to dry out",
        "watering_interval_days": 8,
        "description": "Popular Swiss Cheese Plant featuring large glossy leaves with natural perforations.",
        "price": 35.00,
        "in_stock": 12,
    },
    {
        "name": "Snake Plant",
        "scientific_name": "Dracaena trifasciata",
        "care_difficulty": "Very Easy",
        "light_requirements": "Low to bright indirect light, highly drought tolerant",
        "watering_frequency": "Water every 2-3 weeks; allow soil to dry completely",
        "watering_interval_days": 18,
        "description": "Hardy architectural plant with upright sword-like leaves that purifies indoor air.",
        "price": 24.50,
        "in_stock": 20,
    },
    {
        "name": "Fiddle Leaf Fig",
        "scientific_name": "Ficus lyrata",
        "care_difficulty": "Moderate",
        "light_requirements": "Bright, filtered indirect sunlight",
        "watering_frequency": "Water weekly when the top inch of soil feels dry to touch",
        "watering_interval_days": 7,
        "description": "Dramatic statement plant with large violin-shaped textured leaves.",
        "price": 55.00,
        "in_stock": 6,
    },
    {
        "name": "Golden Pothos",
        "scientific_name": "Epipremnum aureum",
        "care_difficulty": "Very Easy",
        "light_requirements": "Low to medium indirect light",
        "watering_frequency": "Water every 7-10 days when top 1-2 inches are dry",
        "watering_interval_days": 8,
        "description": "Fast-growing trailing vine with heart-shaped variegated green and gold leaves.",
        "price": 18.00,
        "in_stock": 25,
    },
    {
        "name": "Peace Lily",
        "scientific_name": "Spathiphyllum",
        "care_difficulty": "Easy",
        "light_requirements": "Medium to low indirect light",
        "watering_frequency": "Water weekly; leaves drop when thirsty making it easy to read",
        "watering_interval_days": 6,
        "description": "Lush tropical perennial with glossy dark foliage and striking white spathe blooms.",
        "price": 22.00,
        "in_stock": 10,
    },
]


def seed_database() -> None:
    print(f"Connecting to Firestore with project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    plants_ref = db.collection(COLLECTION_NAME)

    for plant in SAMPLE_PLANTS:
        doc_id = (
            plant["name"]
            .lower()
            .replace(" ", "-")
            .replace("(", "")
            .replace(")", "")
        )
        plants_ref.document(doc_id).set(plant)
        print(f"  ✓ Seeded: {plant['name']} (ID: {doc_id})")

    print(
        f"\nSuccessfully seeded {len(SAMPLE_PLANTS)} plants into '{COLLECTION_NAME}' collection."
    )


if __name__ == "__main__":
    seed_database()
