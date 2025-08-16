from typing import Optional, List
from sqlalchemy.orm import Session
from sqlmodel import select
from sqlalchemy import and_
from src.models.tag import Tag
from src.models.recipe_tag import RecipeTag
from datetime import datetime, timezone
import uuid


class TagService:
    """
    Service layer for tag-related business logic.
    
    This service handles all tag operations and encapsulates
    the business logic for tag management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the tag service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """
        Get a tag by its ID.
        
        Args:
            tag_id: The tag's ID
            
        Returns:
            Tag object if found, None otherwise
        """
        statement = select(Tag).where(Tag.id == tag_id)
        return self.db.exec(statement).first()
    
    def get_tag_by_uuid(self, tag_uuid: str) -> Optional[Tag]:
        """
        Get a tag by its UUID.
        
        Args:
            tag_uuid: The tag's UUID
            
        Returns:
            Tag object if found, None otherwise
        """
        statement = select(Tag).where(Tag.uuid == tag_uuid)
        return self.db.exec(statement).first()
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Get a tag by its normalized name.
        
        Args:
            name: The tag's name (will be normalized)
            
        Returns:
            Tag object if found, None otherwise
        """
        normalized_name = Tag.normalize_name(name)
        statement = select(Tag).where(Tag.name == normalized_name)
        return self.db.exec(statement).first()
    
    def get_all_tags(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get all tags with pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with tags, total count, limit, and offset
        """
        # Get tags for current page
        statement = select(Tag).offset(offset).limit(limit).order_by(Tag.name)
        tags = self.db.exec(statement).all()
        
        # Get total count
        count_statement = select(Tag)
        total = len(self.db.exec(count_statement).all())
        
        return {
            "tags": tags,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def search_tags(self, name: Optional[str] = None, limit: int = 100, offset: int = 0) -> dict:
        """
        Search tags based on criteria with pagination.
        
        Args:
            name: Filter by partial tag name (case-insensitive)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with tags, total count, limit, and offset
        """
        # Build base statement
        statement = select(Tag)
        count_statement = select(Tag)
        
        # Build filters
        filters = []
        
        if name:
            normalized_name = Tag.normalize_name(name)
            filters.append(Tag.name.ilike(f"%{normalized_name}%"))
        
        # Apply filters if any
        if filters:
            statement = statement.where(and_(*filters))
            count_statement = count_statement.where(and_(*filters))
        
        # Add pagination and ordering
        statement = statement.offset(offset).limit(limit).order_by(Tag.name)
        
        # Execute queries
        tags = self.db.exec(statement).all()
        total = len(self.db.exec(count_statement).all())
        
        return {
            "tags": tags,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def create_tag(self, name: str) -> Tag:
        """
        Create a new tag with name uniqueness check.
        
        Args:
            name: Tag name (will be normalized)
            
        Returns:
            Created Tag object
            
        Raises:
            ValueError: If tag name already exists or validation fails
        """
        # Normalize the name
        normalized_name = Tag.normalize_name(name)
        
        # Check if tag already exists
        existing_tag = self.get_tag_by_name(normalized_name)
        if existing_tag:
            raise ValueError(f"Tag '{normalized_name}' already exists")
        
        # Create new tag
        current_time_utc = datetime.now(timezone.utc)
        new_tag = Tag(
            name=normalized_name,
            created_at=current_time_utc,
            updated_at=current_time_utc,
            uuid=str(uuid.uuid4())
        )
        
        # Add to database and commit the transaction
        self.db.add(new_tag)
        self.db.flush()  # Flush to get database-generated values like ID
        self.db.commit()  # Commit the transaction to persist the tag
        self.db.refresh(new_tag)  # Ensure object is up-to-date
        
        return new_tag
    
    def update_tag(self, tag_id: int, name: str) -> Tag:
        """
        Update a tag's name.
        
        Args:
            tag_id: The ID of the tag to update
            name: New tag name (will be normalized)
            
        Returns:
            Updated Tag object
            
        Raises:
            ValueError: If tag not found, name already taken, or validation fails
        """
        # Check if tag exists first
        existing_tag = self.get_tag(tag_id)
        if not existing_tag:
            raise ValueError("Tag not found")
        
        # Normalize the new name
        normalized_name = Tag.normalize_name(name)
        
        # Check if new name is already taken by another tag
        name_check = self.get_tag_by_name(normalized_name)
        if name_check and name_check.id != tag_id:
            raise ValueError(f"Tag name '{normalized_name}' already exists")
        
        # Update the tag
        existing_tag.name = normalized_name
        existing_tag.updated_at = datetime.now(timezone.utc)
        
        # Flush to persist changes and commit
        self.db.flush()
        self.db.commit()  # Commit the transaction to persist changes
        self.db.refresh(existing_tag)
        
        return existing_tag
    
    def delete_tag(self, tag_id: int) -> None:
        """
        Delete a tag by its ID.
        
        Args:
            tag_id: The ID of the tag to delete
        
        Raises:
            ValueError: If tag not found or has existing associations
        """
        # Check if tag exists
        existing_tag = self.get_tag(tag_id)
        if not existing_tag:
            raise ValueError("Tag not found")
        
        # Check if tag has any associations
        associations = self.db.exec(
            select(RecipeTag).where(RecipeTag.tag_id == tag_id)
        ).all()
        
        if associations:
            raise ValueError(f"Cannot delete tag '{existing_tag.name}' - it is associated with {len(associations)} recipe(s)")
        
        # Delete the tag and commit
        self.db.delete(existing_tag)
        self.db.flush()
        self.db.commit()  # Commit the transaction to persist deletion
    
    def get_tags_for_recipe(self, recipe_id: int) -> List[Tag]:
        """
        Get all tags associated with a specific recipe.
        
        Args:
            recipe_id: The ID of the recipe
            
        Returns:
            List of Tag objects associated with the recipe
        """
        statement = select(Tag).join(RecipeTag).where(RecipeTag.recipe_id == recipe_id)
        return self.db.exec(statement).all()
    
    def add_tag_to_recipe(self, recipe_id: int, tag_id: int) -> RecipeTag:
        """
        Add a tag to a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            tag_id: The ID of the tag to add
            
        Returns:
            Created RecipeTag object
            
        Raises:
            ValueError: If recipe or tag not found, or association already exists
        """
        # Check if recipe exists (basic check - could be enhanced with Recipe model)
        # For now, we'll assume the recipe exists and let the foreign key constraint handle it
        
        # Check if tag exists
        tag = self.get_tag(tag_id)
        if not tag:
            raise ValueError("Tag not found")
        
        # Check if association already exists
        existing_association = self.db.exec(
            select(RecipeTag).where(
                and_(
                    RecipeTag.recipe_id == recipe_id,
                    RecipeTag.tag_id == tag_id
                )
            )
        ).first()
        
        if existing_association:
            raise ValueError("Tag is already associated with this recipe")
        
        # Create the association
        current_time_utc = datetime.now(timezone.utc)
        recipe_tag = RecipeTag(
            recipe_id=recipe_id,
            tag_id=tag_id,
            created_at=current_time_utc,
            updated_at=current_time_utc
        )
        
        self.db.add(recipe_tag)
        
        # Increment the tag's recipe counter
        tag.recipe_counter += 1
        tag.updated_at = current_time_utc
        
        self.db.flush()
        self.db.commit()
        self.db.refresh(recipe_tag)
        
        return recipe_tag
    
    def add_tags_to_recipe(self, recipe_id: int, tag_ids: List[int]) -> List[RecipeTag]:
        """
        Add multiple tags to a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            tag_ids: List of tag IDs to add
            
        Returns:
            List of created RecipeTag objects
            
        Raises:
            ValueError: If any tag not found, or any association already exists
        """
        if not tag_ids:
            return []
        
        # Validate all tags exist and get them
        tags = []
        for tag_id in tag_ids:
            tag = self.get_tag(tag_id)
            if not tag:
                raise ValueError(f"Tag with ID {tag_id} not found")
            tags.append(tag)
        
        # Check for existing associations
        existing_associations = self.db.exec(
            select(RecipeTag).where(
                and_(
                    RecipeTag.recipe_id == recipe_id,
                    RecipeTag.tag_id.in_(tag_ids)
                )
            )
        ).all()
        
        if existing_associations:
            existing_tag_ids = [rt.tag_id for rt in existing_associations]
            raise ValueError(f"Tags with IDs {existing_tag_ids} are already associated with this recipe")
        
        # Create all associations
        current_time_utc = datetime.now(timezone.utc)
        recipe_tags = []
        
        for tag_id in tag_ids:
            recipe_tag = RecipeTag(
                recipe_id=recipe_id,
                tag_id=tag_id,
                created_at=current_time_utc,
                updated_at=current_time_utc
            )
            recipe_tags.append(recipe_tag)
            self.db.add(recipe_tag)
        
        # Increment recipe counters for all tags
        for tag in tags:
            tag.recipe_counter += 1
            tag.updated_at = current_time_utc
        
        self.db.flush()
        self.db.commit()
        
        # Refresh all created objects
        for recipe_tag in recipe_tags:
            self.db.refresh(recipe_tag)
        
        return recipe_tags
    
    def remove_tag_from_recipe(self, recipe_id: int, tag_id: int) -> None:
        """
        Remove a tag from a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            tag_id: The ID of the tag to remove
            
        Raises:
            ValueError: If association not found
        """
        # Find the association
        association = self.db.exec(
            select(RecipeTag).where(
                and_(
                    RecipeTag.recipe_id == recipe_id,
                    RecipeTag.tag_id == tag_id
                )
            )
        ).first()
        
        if not association:
            raise ValueError("Tag is not associated with this recipe")
        
        # Get the tag to update its counter
        tag = self.get_tag(tag_id)
        if tag:
            # Decrement the tag's recipe counter
            tag.recipe_counter = max(0, tag.recipe_counter - 1)  # Ensure counter doesn't go below 0
            tag.updated_at = datetime.now(timezone.utc)
        
        # Delete the association
        self.db.delete(association)
        self.db.flush()
        self.db.commit()
    
    def get_popular_tags(self, limit: int = 10) -> List[dict]:
        """
        Get the most popular tags based on usage count.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of dictionaries with tag info and usage count
        """
        # Get tags ordered by recipe_counter (descending) and then by name
        statement = select(Tag).order_by(Tag.recipe_counter.desc(), Tag.name).limit(limit)
        tags = self.db.exec(statement).all()
        
        return [{"tag": tag, "usage_count": tag.recipe_counter} for tag in tags]
