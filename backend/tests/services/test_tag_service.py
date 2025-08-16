import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from src.services.tag_service import TagService
from src.models.tag import Tag
from src.models.recipe_tag import RecipeTag
from sqlmodel import select
from datetime import datetime
from sqlalchemy import and_


class TestTagService:
    """Test cases for TagService."""
    
    def test_tag_service_initialization(self):
        """Test that TagService is properly initialized with database session."""
        # Arrange
        mock_db = Mock()
        
        # Act
        tag_service = TagService(mock_db)
        
        # Assert
        assert tag_service.db == mock_db
    
    def test_get_tag_found(self):
        """Test getting a tag that exists."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(
            id=1,
            uuid="test-uuid",
            name="breakfast",
            recipe_counter=0
        )
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.first.return_value = mock_tag
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag(1)
        
        # Assert
        assert result == mock_tag
        mock_db.exec.assert_called_once()
    
    def test_get_tag_not_found(self):
        """Test getting a tag that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock the database execution to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag(999)
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_tag_by_uuid_found(self):
        """Test getting a tag by UUID that exists."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(
            id=1,
            uuid="test-uuid",
            name="breakfast",
            recipe_counter=0
        )
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.first.return_value = mock_tag
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag_by_uuid("test-uuid")
        
        # Assert
        assert result == mock_tag
        mock_db.exec.assert_called_once()
    
    def test_get_tag_by_uuid_not_found(self):
        """Test getting a tag by UUID that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock the database execution to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag_by_uuid("non-existent-uuid")
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_tag_by_name_found(self):
        """Test getting a tag by name that exists."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(
            id=1,
            uuid="test-uuid",
            name="breakfast",
            recipe_counter=0
        )
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.first.return_value = mock_tag
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag_by_name("Breakfast")
        
        # Assert
        assert result == mock_tag
        mock_db.exec.assert_called_once()
    
    def test_get_tag_by_name_not_found(self):
        """Test getting a tag by name that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock the database execution to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tag_by_name("non-existent-tag")
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_all_tags_with_pagination(self):
        """Test getting all tags with pagination."""
        # Arrange
        mock_db = Mock()
        mock_tags = [
            Tag(id=1, uuid="uuid1", name="breakfast", recipe_counter=0),
            Tag(id=2, uuid="uuid2", name="dinner", recipe_counter=0)
        ]
        
        # Mock the database execution for tags
        mock_exec_tags = Mock()
        mock_exec_tags.all.return_value = mock_tags
        mock_exec_tags.return_value = mock_exec_tags
        
        # Mock the database execution for count
        mock_exec_count = Mock()
        mock_exec_count.all.return_value = mock_tags
        mock_exec_count.return_value = mock_exec_count
        
        mock_db.exec.side_effect = [mock_exec_tags, mock_exec_count]
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_all_tags(limit=10, offset=0)
        
        # Assert
        assert result["tags"] == mock_tags
        assert result["total"] == 2
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert mock_db.exec.call_count == 2
    
    def test_search_tags_with_name_filter(self):
        """Test searching tags with name filter."""
        # Arrange
        mock_db = Mock()
        mock_tags = [Tag(id=1, uuid="uuid1", name="breakfast", recipe_counter=0)]
        
        # Mock the database execution for tags
        mock_exec_tags = Mock()
        mock_exec_tags.all.return_value = mock_tags
        mock_exec_tags.return_value = mock_exec_tags
        
        # Mock the database execution for count
        mock_exec_count = Mock()
        mock_exec_count.all.return_value = mock_tags
        mock_exec_count.return_value = mock_exec_count
        
        mock_db.exec.side_effect = [mock_exec_tags, mock_exec_count]
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.search_tags(name="break", limit=10, offset=0)
        
        # Assert
        assert result["tags"] == mock_tags
        assert result["total"] == 1
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert mock_db.exec.call_count == 2
    
    def test_create_tag_success(self):
        """Test creating a new tag successfully."""
        # Arrange
        mock_db = Mock()
        
        # Mock get_tag_by_name to return None (tag doesn't exist)
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.create_tag("Breakfast")
        
        # Assert
        assert result.name == "breakfast"  # Normalized
        assert result.uuid is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_tag_already_exists(self):
        """Test creating a tag that already exists."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="existing-uuid", name="breakfast", recipe_counter=0)
        
        # Mock get_tag_by_name to return existing tag
        mock_exec = Mock()
        mock_exec.first.return_value = existing_tag
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag 'breakfast' already exists"):
            tag_service.create_tag("Breakfast")
    
    def test_update_tag_success(self):
        """Test updating a tag successfully."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="test-uuid", name="old-name", recipe_counter=0)
        
        # Mock get_tag to return existing tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = existing_tag
        
        # Mock get_tag_by_name to return None (new name doesn't exist)
        mock_exec_name = Mock()
        mock_exec_name.first.return_value = None
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_name]
        
        # Mock database operations
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.update_tag(1, "New Name")
        
        # Assert
        assert result.name == "new name"  # Normalized
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_tag_not_found(self):
        """Test updating a tag that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock get_tag to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag not found"):
            tag_service.update_tag(999, "New Name")
    
    def test_update_tag_name_already_exists(self):
        """Test updating a tag with a name that already exists."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="test-uuid", name="old-name", recipe_counter=0)
        conflicting_tag = Tag(id=2, uuid="conflict-uuid", name="new-name", recipe_counter=0)
        
        # Mock get_tag to return existing tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = existing_tag
        
        # Mock get_tag_by_name to return conflicting tag
        mock_exec_name = Mock()
        mock_exec_name.first.return_value = conflicting_tag
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_name]
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag name 'new name' already exists"):
            tag_service.update_tag(1, "New Name")
    
    def test_delete_tag_success(self):
        """Test deleting a tag successfully."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="test-uuid", name="breakfast", recipe_counter=0)
        
        # Mock get_tag to return existing tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = existing_tag
        
        # Mock check for associations to return empty list
        mock_exec_assoc = Mock()
        mock_exec_assoc.all.return_value = []
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_assoc]
        
        # Mock database operations
        mock_db.delete = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        tag_service.delete_tag(1)
        
        # Assert
        mock_db.delete.assert_called_once_with(existing_tag)
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_delete_tag_not_found(self):
        """Test deleting a tag that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock get_tag to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag not found"):
            tag_service.delete_tag(999)
    
    def test_delete_tag_with_associations(self):
        """Test deleting a tag that has associations."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="test-uuid", name="breakfast", recipe_counter=2)
        
        # Mock get_tag to return existing tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = existing_tag
        
        # Mock check for associations to return existing associations
        mock_exec_assoc = Mock()
        mock_exec_assoc.all.return_value = [RecipeTag(recipe_id=1, tag_id=1), RecipeTag(recipe_id=2, tag_id=1)]
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_assoc]
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete tag 'breakfast' - it is associated with 2 recipe\\(s\\)"):
            tag_service.delete_tag(1)
    
    def test_get_tags_for_recipe(self):
        """Test getting tags for a specific recipe."""
        # Arrange
        mock_db = Mock()
        mock_tags = [
            Tag(id=1, uuid="uuid1", name="breakfast", recipe_counter=0),
            Tag(id=2, uuid="uuid2", name="quick", recipe_counter=0)
        ]
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.all.return_value = mock_tags
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_tags_for_recipe(1)
        
        # Assert
        assert result == mock_tags
        mock_db.exec.assert_called_once()
    
    def test_add_tag_to_recipe_internal_success(self):
        """Test adding a tag to a recipe internally (no commit)."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=0)
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        # Mock check for existing association to return None
        mock_exec_check = Mock()
        mock_exec_check.first.return_value = None
        
        # Mock database operations for creating association
        mock_db.add = Mock()
        mock_db.flush = Mock()
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_check]
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service._add_tag_to_recipe_internal(1, 1)
        
        # Assert
        assert result.recipe_id == 1
        assert result.tag_id == 1
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        # Should NOT call commit
        mock_db.commit.assert_not_called()
    
    def test_add_tag_to_recipe_internal_tag_not_found(self):
        """Test adding a non-existent tag to a recipe internally."""
        # Arrange
        mock_db = Mock()
        
        # Mock get_tag to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag not found"):
            tag_service._add_tag_to_recipe_internal(1, 999)
    
    def test_add_tag_to_recipe_internal_already_associated(self):
        """Test adding a tag that's already associated with the recipe internally."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=0)
        existing_association = RecipeTag(recipe_id=1, tag_id=1)
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        # Mock check for existing association to return existing association
        mock_exec_check = Mock()
        mock_exec_check.first.return_value = existing_association
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_check]
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag is already associated with this recipe"):
            tag_service._add_tag_to_recipe_internal(1, 1)
    
    def test_remove_tag_from_recipe_internal_success(self):
        """Test removing a tag from a recipe internally (no commit)."""
        # Arrange
        mock_db = Mock()
        existing_association = RecipeTag(recipe_id=1, tag_id=1)
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=5)
        
        # Mock find association to return existing association
        mock_exec_assoc = Mock()
        mock_exec_assoc.first.return_value = existing_association
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        mock_db.exec.side_effect = [mock_exec_assoc, mock_exec_get]
        
        # Mock database operations
        mock_db.delete = Mock()
        mock_db.flush = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        tag_service._remove_tag_from_recipe_internal(1, 1)
        
        # Assert
        assert mock_tag.recipe_counter == 4  # Should be decremented
        mock_db.delete.assert_called_once_with(existing_association)
        mock_db.flush.assert_called_once()
        # Should NOT call commit
        mock_db.commit.assert_not_called()
    
    def test_remove_tag_from_recipe_internal_not_associated(self):
        """Test removing a tag that's not associated with the recipe internally."""
        # Arrange
        mock_db = Mock()
        
        # Mock find association to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Tag is not associated with this recipe"):
            tag_service._remove_tag_from_recipe_internal(1, 999)
    
    def test_get_popular_tags(self):
        """Test getting popular tags."""
        # Arrange
        mock_db = Mock()
        mock_tags = [
            Tag(id=1, uuid="uuid1", name="breakfast", recipe_counter=5),
            Tag(id=2, uuid="uuid2", name="dinner", recipe_counter=3),
            Tag(id=3, uuid="uuid3", name="dessert", recipe_counter=0)
        ]
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.all.return_value = mock_tags
        mock_db.exec.return_value = mock_exec
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.get_popular_tags(limit=5)
        
        # Assert
        assert len(result) == 3
        assert result[0]["tag"] == mock_tags[0]
        assert result[0]["usage_count"] == 5
        assert result[1]["tag"] == mock_tags[1]
        assert result[1]["usage_count"] == 3
        assert result[2]["tag"] == mock_tags[2]
        assert result[2]["usage_count"] == 0
        mock_db.exec.assert_called_once()

    def test_update_recipe_tags_success(self):
        """Test updating recipe tags successfully."""
        # Arrange
        mock_db = Mock()
        mock_tags = [
            Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=2),
            Tag(id=2, uuid="tag-uuid2", name="quick", recipe_counter=1),
            Tag(id=3, uuid="tag-uuid3", name="healthy", recipe_counter=0)
        ]
        
        # Mock get_tags_for_recipe to return current tags
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = [mock_tags[0]]  # Only breakfast tag currently
        
        # Mock get_tags_for_recipe
        mock_db.exec.return_value = mock_exec_current
        
        # Mock database operations
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tag_service = TagService(mock_db)
        
        # Mock get_tag method directly to avoid complex database mocking
        def mock_get_tag(tag_id):
            if tag_id == 1:
                return mock_tags[0]  # breakfast
            elif tag_id == 2:
                return mock_tags[1]  # quick
            elif tag_id == 3:
                return mock_tags[2]  # healthy
            return None
        
        tag_service.get_tag = Mock(side_effect=mock_get_tag)
        
        # Mock the internal methods to avoid complex setup
        tag_service._remove_tag_from_recipe_internal = Mock()
        tag_service._add_tag_to_recipe_internal = Mock()
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[2, 3],  # Add quick and healthy
            remove_tag_ids=[1]   # Remove breakfast
        )
        
        # Assert
        assert len(result["added_tags"]) == 2
        assert len(result["removed_tags"]) == 1
        assert result["added_tags"][0].id == 2
        assert result["added_tags"][1].id == 3
        assert result["removed_tags"][0].id == 1
        tag_service._remove_tag_from_recipe_internal.assert_called_once_with(1, 1)
        assert tag_service._add_tag_to_recipe_internal.call_count == 2
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_recipe_tags_duplicate_ids_handled(self):
        """Test that duplicate IDs are automatically removed."""
        # Arrange
        mock_db = Mock()
        mock_tags = [Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=0)]
        
        # Mock get_tags_for_recipe to return current tags
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = []
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tags[0]
        
        mock_db.exec.side_effect = [mock_exec_current, mock_exec_get]
        
        tag_service = TagService(mock_db)
        
        # Mock the internal methods
        tag_service._add_tag_to_recipe_internal = Mock()
        
        # Act - should not raise error, duplicates should be removed
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[1, 1, 1],  # Duplicates
            remove_tag_ids=[]
        )
        
        # Assert - should only call add once for the deduplicated ID
        tag_service._add_tag_to_recipe_internal.assert_called_once_with(1, 1)

    def test_update_recipe_tags_conflicting_ids(self):
        """Test updating recipe tags with conflicting add/remove IDs."""
        # Arrange
        mock_db = Mock()
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[1, 2],
            remove_tag_ids=[2, 3]  # ID 2 appears in both
        )
        
        # Assert
        assert len(result["errors"]) == 1
        assert "Tag IDs [2] appear in both add and remove lists" in result["errors"][0]
        assert len(result["added_tags"]) == 0
        assert len(result["removed_tags"]) == 0

    def test_update_recipe_tags_tag_not_found(self):
        """Test updating recipe tags with non-existent tag."""
        # Arrange
        mock_db = Mock()
        mock_tags = [Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=0)]
        
        # Mock get_tags_for_recipe to return current tags
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = []
        
        # Mock get_tag to return None for non-existent tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = None
        
        mock_db.exec.side_effect = [mock_exec_current, mock_exec_get]
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[999],  # Non-existent tag
            remove_tag_ids=[]
        )
        
        # Assert
        assert len(result["errors"]) == 1
        assert "Tag with ID 999 not found" in result["errors"][0]
        assert len(result["added_tags"]) == 0
        assert len(result["removed_tags"]) == 0

    def test_update_recipe_tags_empty_operations(self):
        """Test updating recipe tags with no operations."""
        # Arrange
        mock_db = Mock()
        mock_tags = [Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=0)]
        
        # Mock get_tags_for_recipe to return current tags
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = mock_tags
        
        mock_db.exec.return_value = mock_exec_current
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[],
            remove_tag_ids=[]
        )
        
        # Assert
        assert len(result["added_tags"]) == 0
        assert len(result["removed_tags"]) == 0
        assert len(result["current_tags"]) == 1
        assert len(result["warnings"]) == 0
        assert len(result["errors"]) == 0
    
    def test_update_recipe_tags_warnings_for_no_ops(self):
        """Test that warnings are generated for no-op operations."""
        # Arrange
        mock_db = Mock()
        mock_tags = [
            Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=0),
            Tag(id=2, uuid="tag-uuid2", name="quick", recipe_counter=0)
        ]
        
        # Mock get_tags_for_recipe to return current tags (only breakfast)
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = [mock_tags[0]]  # Only breakfast currently
        
        # Mock database operations
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_db.exec.return_value = mock_exec_current
        
        tag_service = TagService(mock_db)
        
        # Mock get_tag method directly
        def mock_get_tag(tag_id):
            if tag_id == 1:
                return mock_tags[0]  # breakfast
            elif tag_id == 2:
                return mock_tags[1]  # quick
            return None
        
        tag_service.get_tag = Mock(side_effect=mock_get_tag)
        
        # Mock the internal methods
        tag_service._add_tag_to_recipe_internal = Mock()
        tag_service._remove_tag_from_recipe_internal = Mock()
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[1],    # Try to add breakfast (already associated)
            remove_tag_ids=[2]  # Try to remove quick (not associated)
        )
        
        # Assert
        assert len(result["warnings"]) == 2
        assert "Adding tag 1 was skipped because it is already associated with recipe 1" in result["warnings"][0]
        assert "Removing tag 2 was skipped because it is not associated with recipe 1" in result["warnings"][1]
        assert len(result["added_tags"]) == 0
        assert len(result["removed_tags"]) == 0
        assert len(result["errors"]) == 0
    
    def test_update_recipe_tags_database_error(self):
        """Test that database errors are handled and returned in result."""
        # Arrange
        mock_db = Mock()
        mock_tags = [Tag(id=1, uuid="tag-uuid1", name="breakfast", recipe_counter=0)]
        
        # Mock get_tags_for_recipe to return current tags
        mock_exec_current = Mock()
        mock_exec_current.all.return_value = []
        
        # Mock database operations
        mock_db.flush = Mock(side_effect=Exception("Database connection failed"))
        mock_db.rollback = Mock()
        mock_db.refresh = Mock()
        
        mock_db.exec.return_value = mock_exec_current
        
        tag_service = TagService(mock_db)
        
        # Mock get_tag method directly
        tag_service.get_tag = Mock(return_value=mock_tags[0])
        
        # Mock the internal methods
        tag_service._add_tag_to_recipe_internal = Mock()
        
        # Act
        result = tag_service.update_recipe_tags(
            recipe_id=1,
            add_tag_ids=[1],
            remove_tag_ids=[]
        )
        
        # Assert
        assert len(result["errors"]) == 1
        assert "Failed to update recipe tags: Database connection failed" in result["errors"][0]
        # Tags are added to result before flush, so they'll be there even if flush fails
        assert len(result["added_tags"]) == 1
        assert len(result["removed_tags"]) == 0
        mock_db.rollback.assert_called_once()
     
    def test_create_tag_with_normalization(self):
        """Test that tag names are properly normalized when created."""
        # Arrange
        mock_db = Mock()
        
        # Mock get_tag_by_name to return None (tag doesn't exist)
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.create_tag("  BREAKFAST  ")
        
        # Assert
        assert result.name == "breakfast"  # Should be normalized
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_tag_with_normalization(self):
        """Test that tag names are properly normalized when updated."""
        # Arrange
        mock_db = Mock()
        existing_tag = Tag(id=1, uuid="test-uuid", name="old-name", recipe_counter=0)
        
        # Mock get_tag to return existing tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = existing_tag
        
        # Mock get_tag_by_name to return None (new name doesn't exist)
        mock_exec_name = Mock()
        mock_exec_name.first.return_value = None
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_name]
        
        # Mock database operations
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service.update_tag(1, "  NEW NAME  ")
        
        # Assert
        assert result.name == "new name"  # Should be normalized
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_add_tag_to_recipe_internal_increments_counter(self):
        """Test that adding a tag to a recipe internally increments the recipe counter."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=5)
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        # Mock check for existing associations to return None
        mock_exec_check = Mock()
        mock_exec_check.first.return_value = None
        
        mock_db.exec.side_effect = [mock_exec_get, mock_exec_check]
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.flush = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        result = tag_service._add_tag_to_recipe_internal(1, 1)
        
        # Assert
        assert mock_tag.recipe_counter == 6  # Should be incremented
        assert result.recipe_id == 1
        assert result.tag_id == 1
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        # Should NOT call commit (internal method)
        mock_db.commit.assert_not_called()
    
    def test_remove_tag_from_recipe_internal_decrements_counter(self):
        """Test that removing a tag from a recipe internally decrements the recipe counter."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=5)
        existing_association = RecipeTag(recipe_id=1, tag_id=1)
        
        # Mock find association to return existing association
        mock_exec_assoc = Mock()
        mock_exec_assoc.first.return_value = existing_association
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        mock_db.exec.side_effect = [mock_exec_assoc, mock_exec_get]
        
        # Mock database operations
        mock_db.delete = Mock()
        mock_db.flush = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        tag_service._remove_tag_from_recipe_internal(1, 1)
        
        # Assert
        assert mock_tag.recipe_counter == 4  # Should be decremented
        mock_db.delete.assert_called_once_with(existing_association)
        mock_db.flush.assert_called_once()
        # Should NOT call commit (internal method)
        mock_db.commit.assert_not_called()
    
    def test_remove_tag_from_recipe_internal_counter_never_goes_below_zero(self):
        """Test that recipe counter never goes below zero internally."""
        # Arrange
        mock_db = Mock()
        mock_tag = Tag(id=1, uuid="tag-uuid", name="breakfast", recipe_counter=0)
        existing_association = RecipeTag(recipe_id=1, tag_id=1)
        
        # Mock find association to return existing association
        mock_exec_assoc = Mock()
        mock_exec_assoc.first.return_value = existing_association
        
        # Mock get_tag to return tag
        mock_exec_get = Mock()
        mock_exec_get.first.return_value = mock_tag
        
        mock_db.exec.side_effect = [mock_exec_assoc, mock_exec_get]
        
        # Mock database operations
        mock_db.delete = Mock()
        mock_db.flush = Mock()
        
        tag_service = TagService(mock_db)
        
        # Act
        tag_service._remove_tag_from_recipe_internal(1, 1)
        
        # Assert
        assert mock_tag.recipe_counter == 0  # Should stay at 0
        mock_db.delete.assert_called_once_with(existing_association)
        mock_db.flush.assert_called_once()
        # Should NOT call commit (internal method)
        mock_db.commit.assert_not_called()
    

    

    

    

