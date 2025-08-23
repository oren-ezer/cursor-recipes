from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlmodel import select
from sqlalchemy import and_
from src.models.tag import Tag, TagCategory
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
        result = self.db.exec(statement)
        return result.first()
    
    def get_tag_by_uuid(self, tag_uuid: str) -> Optional[Tag]:
        """
        Get a tag by its UUID.
        
        Args:
            tag_uuid: The tag's UUID
            
        Returns:
            Tag object if found, None otherwise
        """
        statement = select(Tag).where(Tag.uuid == tag_uuid)
        result = self.db.exec(statement)
        return result.first()
    
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
        result = self.db.exec(statement)
        return result.first()
    
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
        statement = select(Tag).order_by(Tag.name).offset(offset).limit(limit)
        result = self.db.exec(statement)
        tags = result.all()
        
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
        # Build base query
        statement = select(Tag)
        
        # Add filters
        if name:
            normalized_name = Tag.normalize_name(name)
            statement = statement.where(Tag.name.ilike(f"%{normalized_name}%"))
        
        # Get total count first
        count_statement = statement
        total_tags = self.db.exec(count_statement).all()
        total = len(total_tags)
        
        # Add pagination and ordering
        statement = statement.order_by(Tag.name).offset(offset).limit(limit)
        result = self.db.exec(statement)
        tags = result.all()
        
        return {
            "tags": tags,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def create_tag(self, name: str, category: TagCategory) -> Tag:
        """
        Create a new tag with name uniqueness check.
        
        Args:
            name: Tag name (will be normalized)
            category: Category for the tag (will be converted to string value)
            
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
        
        # Create new tag with string category value
        current_time_utc = datetime.now(timezone.utc)
        new_tag = Tag(
            name=normalized_name,
            category=category.value,  # Use the string value
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
    
    def update_tag(self, tag_id: int, name: str, category: TagCategory) -> Tag:
        """
        Update a tag's name and/or category.
        
        Args:
            tag_id: The ID of the tag to update
            name: New tag name (will be normalized)
            category: New category for the tag
            
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
        
        # Update the tag with string category value
        existing_tag.name = normalized_name
        existing_tag.category = category.value  # Use the string value
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
        statement = select(Tag).join(RecipeTag).where(RecipeTag.recipe_id == recipe_id).order_by(Tag.name)
        result = self.db.exec(statement)
        return result.all()
    
    def _add_tag_to_recipe_internal(self, recipe_id: int, tag_id: int) -> RecipeTag:
        """
        Internal method to add a tag to a recipe without committing.
        
        Args:
            recipe_id: The ID of the recipe
            tag_id: The ID of the tag to add
            
        Returns:
            Created RecipeTag object
            
        Raises:
            ValueError: If recipe or tag not found, or association already exists
        """
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
        
        return recipe_tag
    
    def _remove_tag_from_recipe_internal(self, recipe_id: int, tag_id: int) -> None:
        """
        Internal method to remove a tag from a recipe without committing.
        
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
        
        # Get the tag and decrement its counter
        tag = self.get_tag(tag_id)
        if tag:
            tag.recipe_counter = max(0, tag.recipe_counter - 1)
            tag.updated_at = datetime.now(timezone.utc)
        
        # Delete the association
        self.db.delete(association)
        self.db.flush()
    
    def get_popular_tags(self, limit: int = 10) -> List[dict]:
        """
        Get the most popular tags based on usage count.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of dictionaries with tag info and usage count
        """
        statement = select(Tag).order_by(Tag.recipe_counter.desc(), Tag.name).limit(limit)
        result = self.db.exec(statement)
        tags = result.all()
        
        return [{"tag": tag, "usage_count": tag.recipe_counter} for tag in tags]

    def get_tags_by_category(self, limit: int = 100, offset: int = 0) -> Dict[str, List[Tag]]:
        """
        Get all tags grouped by their categories.
        
        Args:
            limit: Maximum number of tags to return per category
            offset: Number of records to skip
            
        Returns:
            Dictionary with category names as keys and lists of tags as values
        """
        statement = select(Tag).order_by(Tag.category, Tag.name).limit(limit).offset(offset)
        result = self.db.exec(statement)
        tags = result.all()
        
        # Group tags by category
        grouped_tags = {}
        for tag in tags:
            category = tag.category  # Already a string value
            if category not in grouped_tags:
                grouped_tags[category] = []
            grouped_tags[category].append(tag)
        
        return grouped_tags

    def get_tags_with_category_info(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get all tags with category information and grouped structure.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with tags, total count, limit, offset, and grouped structure
        """
        # Get tags for current page
        statement = select(Tag).order_by(Tag.category, Tag.name).limit(limit).offset(offset)
        result = self.db.exec(statement)
        tags = result.all()
        
        # Get total count
        count_statement = select(Tag)
        total = len(self.db.exec(count_statement).all())
        
        # Group tags by category
        grouped_tags = {}
        for tag in tags:
            category = tag.category  # Already a string value
            if category not in grouped_tags:
                grouped_tags[category] = []
            grouped_tags[category].append(tag)
        
        return {
            "tags": tags,
            "grouped_tags": grouped_tags,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def update_recipe_tags(
        self, 
        recipe_id: int, 
        add_tag_ids: List[int] = None, 
        remove_tag_ids: List[int] = None
    ) -> dict:
        """
        Update tags for a recipe by adding and/or removing tags in a single atomic operation.
        
        Args:
            recipe_id: The ID of the recipe
            add_tag_ids: List of tag IDs to add (optional)
            remove_tag_ids: List of tag IDs to remove (optional)
            
        Returns:
            Dictionary with operation results:
            - added_tags: List of tags that were successfully added
            - removed_tags: List of tags that were successfully removed
            - current_tags: List of all tags currently associated with the recipe
            - warnings: List of warning messages for skipped operations (e.g., tag already associated)
            - errors: List of error messages (e.g., tag not found, conflicts, database errors)
            
        Note:
            - Duplicate tag IDs in input lists are automatically removed
            - If a tag ID appears in both add and remove lists, an error is added
            - If a tag to add is already associated, it's skipped with a warning
            - If a tag to remove is not associated, it's skipped with a warning
            - All operations are atomic - either all succeed or all fail
            - No exceptions are raised; errors are returned in the result dictionary and the operation is aborted
        """
        # Initialize result structure
        result = {
            "added_tags": [],
            "removed_tags": [],
            "current_tags": [],
            "warnings": [],
            "errors": []
        }
        
        # Normalize and deduplicate input lists
        add_tag_ids_set = set(add_tag_ids or [])
        remove_tag_ids_set = set(remove_tag_ids or [])

        add_tag_ids = list(add_tag_ids_set)
        remove_tag_ids = list(remove_tag_ids_set)
        
        # Check for conflicts between add and remove lists
        conflicts = remove_tag_ids_set & add_tag_ids_set
        if conflicts:
            result["errors"].append(f"Tag IDs {list(conflicts)} appear in both add and remove lists")
            return result
        
        # Get current tags for the recipe
        current_tags = self.get_tags_for_recipe(recipe_id)
        current_tag_ids = {tag.id for tag in current_tags}
        
        # Calculate what actually needs to be done
        tags_to_add = [tid for tid in add_tag_ids if tid not in current_tag_ids]
        tags_to_remove = [tid for tid in remove_tag_ids if tid in current_tag_ids]
        
        # Validate all tags exist
        all_tag_ids = add_tag_ids_set | remove_tag_ids_set
        for tag_id in all_tag_ids:
            tag = self.get_tag(tag_id)
            if not tag:
                result["errors"].append(f"Tag with ID {tag_id} not found")
        
        if result["errors"]:
            return result
        
        # Add warnings for no-op operations
        for tag_id in add_tag_ids:
            if tag_id in current_tag_ids:
                result["warnings"].append(f"Adding tag {tag_id} was skipped because it is already associated with recipe {recipe_id}")
        
        for tag_id in remove_tag_ids:
            if tag_id not in current_tag_ids:
                result["warnings"].append(f"Removing tag {tag_id} was skipped because it is not associated with recipe {recipe_id}")
        
        try:
            # Process removes first
            for tag_id in tags_to_remove:
                self._remove_tag_from_recipe_internal(recipe_id, tag_id)
                tag = self.get_tag(tag_id)
                if tag:
                    result["removed_tags"].append(tag)
            
            # Process adds
            for tag_id in tags_to_add:
                self._add_tag_to_recipe_internal(recipe_id, tag_id)
                tag = self.get_tag(tag_id)
                if tag:
                    result["added_tags"].append(tag)
            
            # Flush and commit the transaction
            self.db.flush()
            self.db.commit()
            
            # Get updated current tags
            result["current_tags"] = self.get_tags_for_recipe(recipe_id)
            
        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            result["errors"].append(f"Failed to update recipe tags: {str(e)}")
            return result
        
        return result
