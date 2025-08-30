#!/usr/bin/env python3
"""
Script to populate the database with predefined tags and associate them with existing recipes.

This script will:
1. Create predefined tags if they don't exist
2. Associate 0-10 random tags with each existing recipe
3. Update recipe counters for all tags

Usage:
    python scripts/populate_tags.py
"""

import sys
import os
import random
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, create_engine, select
from sqlalchemy import text
from src.models.tag import Tag
from src.models.recipe import Recipe
from src.models.recipe_tag import RecipeTag
from src.core.config import settings
from datetime import datetime, timezone


# Predefined tags to create
PREDEFINED_TAGS = [
    # Meal types
    "breakfast", "lunch", "dinner", "late-night", "snack", "finger-food", "brunch",
    
    # Dietary restrictions
    "vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free", "sugar-free",
    "low-carb", "keto", "paleo", "high-protein", "low-fat", "high-fiber",
    "heart-healthy", "low-sodium", "diabetic-friendly", "high-sugar",
    
    # Course types
    "appetizer", "first-course", "main-course", "side-dish", "dessert", "beverage",
    
    # Cuisines
    "italian", "mexican", "indian", "chinese", "japanese", "thai", "french", "mediterranean",
    
    # Protein sources
    "chicken", "beef", "pork", "fish", "seafood-or-shellfish", "tofu", "eggs",
    
    # Ingredients
    "beans-legumes", "rice", "pasta", "vegetables", "fruit",
    
    # Cooking methods
    "grilling", "baking", "roasting", "frying", "steaming", "raw",
    
    # Special categories
    "kid-friendly", "comfort-food", "holiday", "romantic-dinner", "budget-friendly",
    "one-pot", "super-food"
]


def create_tags(session: Session) -> list[Tag]:
    """Create predefined tags if they don't exist."""
    created_tags = []
    existing_tags = []
    
    for tag_name in PREDEFINED_TAGS:
        # Check if tag already exists
        existing_tag = session.exec(
            select(Tag).where(Tag.name == tag_name.lower().strip())
        ).first()
        
        if existing_tag:
            existing_tags.append(existing_tag)
            print(f"Tag '{tag_name}' already exists (ID: {existing_tag.id})")
        else:
            # Create new tag
            new_tag = Tag(
                name=tag_name.lower().strip(),
                uuid=str(random.randint(1000000, 9999999)),  # Simple UUID for demo
                recipe_counter=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(new_tag)
            session.flush()  # Get the ID
            session.refresh(new_tag)
            created_tags.append(new_tag)
            print(f"Created tag '{tag_name}' (ID: {new_tag.id})")
    
    session.commit()
    print(f"\nCreated {len(created_tags)} new tags")
    print(f"Found {len(existing_tags)} existing tags")
    
    return created_tags + existing_tags


def associate_tags_with_recipes(session: Session, tags: list[Tag]) -> None:
    """Associate 0-10 random tags with each existing recipe."""
    # Get all existing recipes
    recipes = session.exec(select(Recipe)).all()
    
    if not recipes:
        print("No recipes found in the database")
        return
    
    print(f"\nFound {len(recipes)} recipes to associate with tags")
    
    total_associations = 0
    
    for recipe in recipes:
        # Randomly select 0-10 tags for this recipe
        num_tags = random.randint(0, min(10, len(tags)))
        selected_tags = random.sample(tags, num_tags) if num_tags > 0 else []
        
        # Check existing associations to avoid duplicates using raw SQL
        result = session.exec(
            text(f"SELECT tag_id FROM recipe_tags WHERE recipe_id = {recipe.id}")
        ).all()
        existing_tag_ids = {row[0] for row in result} if result else set()
        
        # Only add tags that aren't already associated
        new_tags = [tag for tag in selected_tags if tag.id not in existing_tag_ids]
        
        if new_tags:
            current_time = datetime.now(timezone.utc)
            
            for tag in new_tags:
                try:
                    # Use raw SQL to insert the association with a synthetic ID
                    # Get the next available ID for recipe_tags
                    result = session.exec(text("SELECT COALESCE(MAX(id), 0) + 1 FROM recipe_tags")).first()
                    next_id = result[0] if result else 1
                    
                    session.exec(
                        text(f"""
                        INSERT INTO recipe_tags (id, recipe_id, tag_id, created_at, updated_at)
                        VALUES ({next_id}, {recipe.id}, {tag.id}, '{current_time}', '{current_time}')
                        """)
                    )
                    
                    # Increment tag counter
                    tag.recipe_counter += 1
                    tag.updated_at = current_time
                    
                except Exception as e:
                    print(f"Error adding tag {tag.name} to recipe {recipe.title}: {e}")
                    continue
            
            total_associations += len(new_tags)
            print(f"Recipe '{recipe.title}' (ID: {recipe.id}): Added {len(new_tags)} tags")
        else:
            print(f"Recipe '{recipe.title}' (ID: {recipe.id}): No new tags added (already has {len(existing_tag_ids)} tags)")
    
    session.commit()
    print(f"\nTotal new associations created: {total_associations}")


def main():
    """Main function to populate tags and associate them with recipes."""
    print("Starting tag population script...")
    
    # Get database settings
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        try:
            # Step 1: Create tags
            print("\n=== Creating Tags ===")
            tags = create_tags(session)
            
            # Step 2: Associate tags with recipes
            print("\n=== Associating Tags with Recipes ===")
            associate_tags_with_recipes(session, tags)
            
            # Step 3: Verify results
            print("\n=== Verification ===")
            total_tags = session.exec(select(Tag)).all()
            total_recipes = session.exec(select(Recipe)).all()
            total_associations = session.exec(select(RecipeTag)).all()
            
            print(f"Total tags in database: {len(total_tags)}")
            print(f"Total recipes in database: {len(total_recipes)}")
            print(f"Total recipe-tag associations: {len(total_associations)}")
            
            # Show some popular tags
            popular_tags = session.exec(
                select(Tag).order_by(Tag.recipe_counter.desc()).limit(10)
            ).all()
            
            print(f"\nTop 10 most popular tags:")
            for i, tag in enumerate(popular_tags, 1):
                print(f"  {i}. {tag.name} ({tag.recipe_counter} recipes)")
            
            print("\n✅ Tag population completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during tag population: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()
