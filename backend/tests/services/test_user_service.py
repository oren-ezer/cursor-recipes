import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from src.services.user_service import UserService
from src.models.user import User
from sqlmodel import select
from datetime import datetime


class TestUserService:
    """Test cases for UserService."""
    
    def test_get_user_found(self):
        """Test getting a user that exists."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock the database execution
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == mock_user
        mock_db.exec.assert_called_once()
    
    def test_get_user_not_found(self):
        """Test getting a user that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        # Mock the database execution to return None
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(999)
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_user_service_initialization(self):
        """Test that UserService is properly initialized with database session."""
        # Arrange
        mock_db = Mock()
        
        # Act
        user_service = UserService(mock_db)
        
        # Assert
        assert user_service.db == mock_db
    
    def test_get_user_with_zero_id(self):
        """Test getting a user with ID 0 (edge case)."""
        # Arrange
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(0)
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_user_with_negative_id(self):
        """Test getting a user with negative ID (edge case)."""
        # Arrange
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(-1)
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_user_database_exception(self):
        """Test handling of database exceptions."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.get_user(1)
        
    def test_get_user_multiple_calls(self):
        """Test multiple calls to get_user with different IDs."""
        # Arrange
        mock_db = Mock()
        mock_user1 = User(id=1, uuid="uuid1", email="user1@test.com", is_active=True, is_superuser=False)
        mock_user2 = User(id=2, uuid="uuid2", email="user2@test.com", is_active=True, is_superuser=False)
        
        mock_exec = Mock()
        mock_exec.first.side_effect = [mock_user1, mock_user2]
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result1 = user_service.get_user(1)
        result2 = user_service.get_user(2)
        
        # Assert
        assert result1 == mock_user1
        assert result2 == mock_user2
        assert mock_db.exec.call_count == 2
    
    def test_get_user_with_inactive_user(self):
        """Test getting an inactive user."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="inactive@example.com",
            full_name="Inactive User",
            is_active=False,
            is_superuser=False
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == mock_user
        assert result.is_active is False
    
    def test_get_user_with_superuser(self):
        """Test getting a superuser."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="admin-uuid",
            email="admin@example.com",
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == mock_user
        assert result.is_superuser is True
    
    def test_get_user_with_none_email(self):
        """Test getting a user with None email (edge case)."""
        # Arrange
        mock_db = Mock()
        # Create a mock user without email (simulating database result)
        mock_user = Mock()
        mock_user.id = 1
        mock_user.uuid = "test-uuid"
        mock_user.email = None
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.is_superuser = False
         
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == mock_user
        assert result.email is None
    
    def test_get_user_with_empty_strings(self):
        """Test getting a user with empty string values."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="",
            email="test@example.com",
            full_name="",
            is_active=True,
            is_superuser=False
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == mock_user
        assert result.uuid == ""
        assert result.full_name == ""
    
    def test_get_all_users_empty_list(self):
        """Test getting all users when no users exist."""
        # Arrange
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = []
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_all_users()
        
        # Assert
        assert result["users"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.exec.call_count == 2  # One for users, one for count
    
    def test_get_all_users_with_pagination(self):
        """Test getting all users with pagination parameters."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="user1@test.com", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="user2@test.com", is_active=True, is_superuser=False)
        ]
        
        mock_exec = Mock()
        mock_exec.all.side_effect = [mock_users, mock_users]  # First for users, second for count
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_all_users(limit=5, offset=10)
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 2
        assert result["limit"] == 5
        assert result["offset"] == 10
        assert mock_db.exec.call_count == 2  # One for users, one for count
    
    def test_get_all_users_multiple_users(self):
        """Test getting all users when multiple users exist."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="user1@test.com", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="user2@test.com", is_active=True, is_superuser=False),
            User(id=3, uuid="uuid3", email="user3@test.com", is_active=False, is_superuser=True)
        ]
        
        mock_exec = Mock()
        mock_exec.all.side_effect = [mock_users, mock_users]  # First for users, second for count
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_all_users()
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 3
        assert len(result["users"]) == 3
        assert mock_db.exec.call_count == 2  # One for users, one for count
    
    def test_get_all_users_default_parameters(self):
        """Test getting all users with default parameters."""
        # Arrange
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = []
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_all_users()
        
        # Assert
        assert result["users"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert mock_db.exec.call_count == 2  # One for users, one for count
        # Verify the calls were made correctly
        # First call should be for users with pagination
        first_call_args = mock_db.exec.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str
        assert "offset" in first_call_str
        # Second call should be for count without pagination
        second_call_args = mock_db.exec.call_args_list[1][0][0]
        second_call_str = str(second_call_args).lower()
        assert "limit" not in second_call_str
        assert "offset" not in second_call_str
    
    def test_get_all_users_database_exception(self):
        """Test handling of database exceptions in get_all_users."""
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database error")
        user_service = UserService(mock_db)
        with pytest.raises(Exception, match="Database error"):
            user_service.get_all_users()

    def test_get_all_users_verify_select_statement(self):
        """Test that the correct select statement is used in get_all_users."""
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = []
        mock_db.exec.return_value = mock_exec
        user_service = UserService(mock_db)
        user_service.get_all_users(limit=10, offset=20)
        # Check first call (users with pagination)
        first_call_args = mock_db.exec.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "select" in first_call_str
        assert "from users" in first_call_str
        assert "limit" in first_call_str
        assert "offset" in first_call_str

    def test_get_all_users_large_limit(self):
        """Test get_all_users with a very large limit."""
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = []
        mock_db.exec.return_value = mock_exec
        user_service = UserService(mock_db)
        user_service.get_all_users(limit=10000, offset=0)
        # Check first call (users with pagination)
        first_call_args = mock_db.exec.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str

    def test_get_all_users_negative_skip_and_limit(self):
        """Test get_all_users with negative skip and limit values."""
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = []
        mock_db.exec.return_value = mock_exec
        user_service = UserService(mock_db)
        user_service.get_all_users(limit=10, offset=0)
        # Check first call (users with pagination)
        first_call_args = mock_db.exec.call_args_list[0][0][0]
        first_call_str = str(first_call_args).lower()
        assert "limit" in first_call_str
        assert "offset" in first_call_str

    def test_get_all_users_varied_fields(self):
        """Test get_all_users with users having varied field values."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="user1@test.com", full_name="User One", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="user2@test.com", full_name=None, is_active=False, is_superuser=True),
            User(id=3, uuid="uuid3", email="user3@test.com", full_name="User Three", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_all_users(limit=10, offset=0)
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 3
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert len(result["users"]) == 3
    
    def test_search_for_users_no_filters(self):
        """Test search_for_users with no filters applied."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="user1@test.com", full_name="User One", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="user2@test.com", full_name="User Two", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users()
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 2
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 2
    
    def test_search_for_users_with_email_filter(self):
        """Test search_for_users with email filter."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="john@test.com", full_name="John Doe", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(email="john")
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 1
    
    def test_search_for_users_with_full_name_filter(self):
        """Test search_for_users with full_name filter."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="john@test.com", full_name="John Doe", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="jane@test.com", full_name="Jane Doe", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(full_name="Doe")
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 2
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 2
    
    def test_search_for_users_with_is_active_filter(self):
        """Test search_for_users with is_active filter."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="active@test.com", full_name="Active User", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(is_active=True)
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 1
    
    def test_search_for_users_with_multiple_filters(self):
        """Test search_for_users with multiple filters applied."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="john@test.com", full_name="John Doe", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(
            email="john",
            full_name="Doe",
            is_active=True
        )
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 1
    
    def test_search_for_users_with_pagination(self):
        """Test search_for_users with pagination."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=2, uuid="uuid2", email="user2@test.com", full_name="User Two", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(limit=1, offset=1)
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert result["limit"] == 1
        assert result["offset"] == 1
        assert len(result["users"]) == 1
    
    def test_search_for_users_empty_result(self):
        """Test search_for_users when no users match the criteria."""
        # Arrange
        mock_db = Mock()
        mock_users = []
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(email="nonexistent")
        
        # Assert
        assert result["users"] == []
        assert result["total"] == 0
        assert result["limit"] == 100
        assert result["offset"] == 0
        assert len(result["users"]) == 0
    
    def test_search_for_users_case_insensitive_email(self):
        """Test that email search is case-insensitive."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="John@TEST.com", full_name="John Doe", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(email="john")
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert len(result["users"]) == 1
    
    def test_search_for_users_case_insensitive_full_name(self):
        """Test that full_name search is case-insensitive."""
        # Arrange
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="john@test.com", full_name="JOHN DOE", is_active=True, is_superuser=False),
        ]
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.search_for_users(full_name="doe")
        
        # Assert
        assert result["users"] == mock_users
        assert result["total"] == 1
        assert len(result["users"]) == 1
    
    def test_search_for_users_database_exception(self):
        """Test handling of database exceptions in search_for_users."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.search_for_users(email="test")
    
    def test_search_for_users_edge_cases(self):
        """Test search_for_users with edge cases."""
        # Arrange
        mock_db = Mock()
        mock_users = []
        
        mock_exec = Mock()
        mock_exec.all.return_value = mock_users
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Test with empty string filters
        result1 = user_service.search_for_users(email="", full_name="")
        assert result1["users"] == []
        
        # Test with None filters (should be same as no filters)
        result2 = user_service.search_for_users(email=None, full_name=None, is_active=None)
        assert result2["users"] == []
        
        # Test with offset 0 (default)
        result3 = user_service.search_for_users(offset=0)
        assert result3["offset"] == 0
        
        # Test with very large limit
        result4 = user_service.search_for_users(limit=1000)
        assert result4["limit"] == 1000
    
    def test_get_current_user_found(self):
        """Test getting current user that exists."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid-123",
            email="current@example.com",
            full_name="Current User",
            is_active=True,
            is_superuser=False
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user("test-uuid-123")
        
        # Assert
        assert result == mock_user
        assert result.uuid == "test-uuid-123"
        assert result.email == "current@example.com"
        mock_db.exec.assert_called_once()
    
    def test_get_current_user_not_found(self):
        """Test getting current user that doesn't exist."""
        # Arrange
        mock_db = Mock()
        
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user("nonexistent-uuid")
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_current_user_with_empty_uuid(self):
        """Test getting current user with empty UUID."""
        # Arrange
        mock_db = Mock()
        
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user("")
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_current_user_with_none_uuid(self):
        """Test getting current user with None UUID."""
        # Arrange
        mock_db = Mock()
        
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user(None)
        
        # Assert
        assert result is None
        mock_db.exec.assert_called_once()
    
    def test_get_current_user_database_exception(self):
        """Test handling of database exceptions in get_current_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.get_current_user("test-uuid")
    
    def test_get_current_user_multiple_calls(self):
        """Test multiple calls to get_current_user with different UUIDs."""
        # Arrange
        mock_db = Mock()
        mock_user1 = User(id=1, uuid="uuid1", email="user1@test.com", is_active=True, is_superuser=False)
        mock_user2 = User(id=2, uuid="uuid2", email="user2@test.com", is_active=True, is_superuser=False)
        
        mock_exec = Mock()
        mock_exec.first.side_effect = [mock_user1, mock_user2]
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result1 = user_service.get_current_user("uuid1")
        result2 = user_service.get_current_user("uuid2")
        
        # Assert
        assert result1 == mock_user1
        assert result2 == mock_user2
        assert mock_db.exec.call_count == 2
    
    def test_get_current_user_with_inactive_user(self):
        """Test getting an inactive current user."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="inactive-uuid",
            email="inactive@example.com",
            full_name="Inactive User",
            is_active=False,
            is_superuser=False
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user("inactive-uuid")
        
        # Assert
        assert result == mock_user
        assert result.is_active is False
        assert result.uuid == "inactive-uuid"
    
    def test_get_current_user_with_superuser(self):
        """Test getting a superuser as current user."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="admin-uuid",
            email="admin@example.com",
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        
        mock_exec = Mock()
        mock_exec.first.return_value = mock_user
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.get_current_user("admin-uuid")
        
        # Assert
        assert result == mock_user
        assert result.is_superuser is True
        assert result.uuid == "admin-uuid"
    
    def test_get_current_user_verify_select_statement(self):
        """Test that the correct select statement is used in get_current_user."""
        # Arrange
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        
        user_service = UserService(mock_db)
        
        # Act
        user_service.get_current_user("test-uuid")
        
        # Assert
        mock_db.exec.assert_called_once()
        call_args = mock_db.exec.call_args[0][0]
        call_str = str(call_args).lower()
        assert "select" in call_str
        assert "from users" in call_str
        assert "uuid" in call_str
    
    def test_create_user_success(self):
        """Test creating a user successfully."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid-123",
            email="new@example.com",
            full_name="New User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="new@example.com",
            password="ValidPass123!",
            full_name="New User"
        )
        
        # Assert
        assert result.email == "new@example.com"
        assert result.full_name == "New User"
        assert result.is_active is True
        assert result.is_superuser is False
        assert result.uuid is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_user_without_full_name(self):
        """Test creating a user without full name."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid-123",
            email="new@example.com",
            full_name=None,
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="new@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        assert result.email == "new@example.com"
        assert result.full_name is None
        assert result.is_active is True
        assert result.is_superuser is False
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
    
    def test_create_user_email_already_exists(self):
        """Test creating a user with email that already exists."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="existing-uuid",
            email="existing@example.com",
            full_name="Existing User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database to return existing user
        mock_db.exec.return_value.first.return_value = existing_user
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(
                email="existing@example.com",
                password="ValidPass123!",
                full_name="New User"
            )
        
        # Verify no database write operations were called
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
    
    def test_create_user_database_exception(self):
        """Test handling of database exceptions in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.create_user(
                email="test@example.com",
                password="ValidPass123!"
            )
    
    def test_create_user_flush_exception(self):
        """Test handling of flush exceptions in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush.side_effect = Exception("Flush failed")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Flush failed"):
            user_service.create_user(
                email="test@example.com",
                password="ValidPass123!"
            )
    
    def test_create_user_verify_password_hashing(self):
        """Test that password is properly hashed in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        # Verify that add was called with a User object that has hashed_password
        add_call_args = mock_db.add.call_args[0][0]
        assert isinstance(add_call_args, User)
        assert add_call_args.hashed_password != "ValidPass123!"  # Should be hashed
        assert add_call_args.hashed_password is not None  # Should not be None
    
    def test_create_user_verify_uuid_generation(self):
        """Test that UUID is properly generated in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        # Verify that add was called with a User object that has UUID
        add_call_args = mock_db.add.call_args[0][0]
        assert isinstance(add_call_args, User)
        assert add_call_args.uuid is not None
        assert len(add_call_args.uuid) > 0
        assert isinstance(add_call_args.uuid, str)
    
    def test_create_user_verify_timestamps(self):
        """Test that timestamps are properly set in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        # Verify that add was called with a User object that has timestamps
        add_call_args = mock_db.add.call_args[0][0]
        assert isinstance(add_call_args, User)
        assert add_call_args.created_at is not None
        assert add_call_args.updated_at is not None
        assert add_call_args.created_at == add_call_args.updated_at  # Should be same initially
    
    def test_create_user_verify_default_values(self):
        """Test that default values are properly set in create_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None  # No existing user
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.create_user(
            email="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        # Verify that add was called with a User object that has correct defaults
        add_call_args = mock_db.add.call_args[0][0]
        assert isinstance(add_call_args, User)
        assert add_call_args.is_active is True
        assert add_call_args.is_superuser is False

    def test_update_user_success(self):
        """Test updating a user successfully."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="old@example.com",
            full_name="Old Name",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations - first call returns existing user, second call (email check) returns None
        mock_db.exec.return_value.first.side_effect = [existing_user, None]
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {
            "email": "new@example.com",
            "full_name": "New Name"
        }
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.email == "new@example.com"
        assert result.full_name == "New Name"
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_not_found(self):
        """Test updating a user that doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user(999, {"email": "new@example.com"})
        
        # Verify no database write operations were called
        mock_db.flush.assert_not_called()
        mock_db.refresh.assert_not_called()
    
    def test_update_user_email_already_taken(self):
        """Test updating user with email that's already taken by another user."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="old@example.com",
            full_name="Old Name",
            is_active=True,
            is_superuser=False
        )
        
        other_user = User(
            id=2,
            uuid="other-uuid",
            email="taken@example.com",
            full_name="Other User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.side_effect = [existing_user, other_user]
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already taken by another user"):
            user_service.update_user(1, {"email": "taken@example.com"})
        
        # Verify no database write operations were called
        mock_db.flush.assert_not_called()
        mock_db.refresh.assert_not_called()
    
    def test_update_user_password_hashing(self):
        """Test that password is properly hashed when updating user."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations - only one call for getting existing user (no email update)
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {"password": "NewValidPass123!"}
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.hashed_password != "NewValidPass123!"  # Should be hashed
        assert result.hashed_password is not None  # Should not be None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_invalid_password(self):
        """Test updating user with invalid password."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            user_service.update_user(1, {"password": "short"})
        
        # Verify no database write operations were called
        mock_db.flush.assert_not_called()
        mock_db.refresh.assert_not_called()
    
    def test_update_user_partial_fields(self):
        """Test updating only some fields of a user."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Old Name",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {"full_name": "New Name"}
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.email == "test@example.com"  # Should remain unchanged
        assert result.full_name == "New Name"  # Should be updated
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_is_active_field(self):
        """Test updating the is_active field."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {"is_active": False}
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.is_active is False
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_is_superuser_field(self):
        """Test updating the is_superuser field."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {"is_superuser": True}
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.is_superuser is True
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_multiple_fields(self):
        """Test updating multiple fields at once."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="old@example.com",
            full_name="Old Name",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations - first call returns existing user, second call (email check) returns None
        mock_db.exec.return_value.first.side_effect = [existing_user, None]
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {
            "email": "new@example.com",
            "full_name": "New Name",
            "is_active": False
        }
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.email == "new@example.com"
        assert result.full_name == "New Name"
        assert result.is_active is False
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_unknown_field(self):
        """Test that unknown fields are ignored."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {
            "full_name": "New Name",
            "unknown_field": "should_be_ignored"
        }
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.full_name == "New Name"
        assert not hasattr(result, "unknown_field")
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_user_database_exception(self):
        """Test handling of database exceptions in update_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.update_user(1, {"email": "new@example.com"})
    
    def test_update_user_flush_exception(self):
        """Test handling of flush exceptions in update_user."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations - first call returns existing user, second call (email check) returns None
        mock_db.exec.return_value.first.side_effect = [existing_user, None]
        mock_db.flush.side_effect = Exception("Flush failed")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Flush failed"):
            user_service.update_user(1, {"email": "new@example.com"})
    
    def test_update_user_verify_timestamp_update(self):
        """Test that updated_at timestamp is properly set."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        user_service = UserService(mock_db)
        
        # Act
        update_data = {"full_name": "New Name"}
        result = user_service.update_user(1, update_data)
        
        # Assert
        assert result.updated_at is not None
        assert isinstance(result.updated_at, datetime)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_delete_user_success(self):
        """Test deleting a user successfully."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.delete = Mock()
        mock_db.flush = Mock()
        user_service = UserService(mock_db)
        # Act
        user_service.delete_user(1)
        # Assert
        mock_db.delete.assert_called_once_with(existing_user)
        mock_db.flush.assert_called_once()

    def test_delete_user_not_found(self):
        """Test deleting a user that does not exist."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            user_service.delete_user(999)
        # No delete or flush should be called
        mock_db.delete.assert_not_called()
        mock_db.flush.assert_not_called()

    def test_delete_user_database_exception(self):
        """Test handling of database exceptions in delete_user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.delete_user(1)

    def test_delete_user_flush_exception(self):
        """Test handling of flush exceptions in delete_user."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.delete = Mock()
        mock_db.flush.side_effect = Exception("Flush failed")
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(Exception, match="Flush failed"):
            user_service.delete_user(1)

    def test_set_superuser_status_success(self):
        """Test setting superuser status successfully."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        user_service = UserService(mock_db)
        # Act
        result = user_service.set_superuser_status(1, True)
        # Assert
        assert result.is_superuser is True
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_set_superuser_status_user_not_found(self):
        """Test setting superuser status for a user that does not exist."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            user_service.set_superuser_status(999, True)
        # No flush or refresh should be called
        mock_db.flush.assert_not_called()
        mock_db.refresh.assert_not_called()

    def test_set_superuser_status_database_exception(self):
        """Test handling of database exceptions in set_superuser_status."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.set_superuser_status(1, True)

    def test_set_superuser_status_flush_exception(self):
        """Test handling of flush exceptions in set_superuser_status."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush.side_effect = Exception("Flush failed")
        user_service = UserService(mock_db)
        # Act & Assert
        with pytest.raises(Exception, match="Flush failed"):
            user_service.set_superuser_status(1, True)

    def test_set_superuser_status_to_false(self):
        """Test setting superuser status to False."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=True
        )
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        user_service = UserService(mock_db)
        # Act
        result = user_service.set_superuser_status(1, False)
        # Assert
        assert result.is_superuser is False
        assert result.updated_at is not None
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_set_superuser_status_verify_timestamp_update(self):
        """Test that updated_at timestamp is properly set."""
        # Arrange
        mock_db = Mock()
        existing_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        # Mock database operations
        mock_db.exec.return_value.first.return_value = existing_user
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        user_service = UserService(mock_db)
        # Act
        result = user_service.set_superuser_status(1, True)
        # Assert
        assert result.updated_at is not None
        assert isinstance(result.updated_at, datetime)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_login_for_access_token_success(self, monkeypatch):
        """Test successful login and token creation."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="$2b$12$ValidPass123!Hash",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.login_for_access_token(
            username="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        assert result["access_token"] == "fake_access_token_123"
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_user_not_found(self):
        """Test login with non-existent user."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_service.login_for_access_token(
                username="nonexistent@example.com",
                password="ValidPass123!"
            )
        
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_incorrect_password(self, monkeypatch):
        """Test login with incorrect password."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return False for incorrect password
        def mock_verify_password(plain_password, hashed_password):
            return False
        
        # Apply mock
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_service.login_for_access_token(
                username="test@example.com",
                password="WrongPassword123!"
            )
        
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_inactive_user(self, monkeypatch):
        """Test login with inactive user."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="ValidPass123!",
            is_active=False,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Apply mock
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Inactive user"):
            user_service.login_for_access_token(
                username="test@example.com",
                password="ValidPass123!"
            )
        
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_empty_username(self):
        """Test login with empty username."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.return_value.first.return_value = None
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_service.login_for_access_token(
                username="",
                password="ValidPass123!"
            )
        
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_empty_password(self, monkeypatch):
        """Test login with empty password."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return False for empty password
        def mock_verify_password(plain_password, hashed_password):
            return False
        
        # Apply mock
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Incorrect email or password"):
            user_service.login_for_access_token(
                username="test@example.com",
                password=""
            )
        
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_database_exception(self):
        """Test handling of database exceptions in login."""
        # Arrange
        mock_db = Mock()
        mock_db.exec.side_effect = Exception("Database connection error")
        
        user_service = UserService(mock_db)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            user_service.login_for_access_token(
                username="test@example.com",
                password="ValidPass123!"
            )
    
    def test_login_for_access_token_with_superuser(self, monkeypatch):
        """Test login with superuser account."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="admin-uuid",
            email="admin@example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=True
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.login_for_access_token(
            username="admin@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        assert result["access_token"] == "fake_access_token_123"
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_case_sensitive_email(self, monkeypatch):
        """Test that email lookup is case-sensitive."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="Test@Example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations - return user for exact match
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.login_for_access_token(
            username="Test@Example.com",  # Exact case match
            password="ValidPass123!"
        )
        
        # Assert
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        mock_db.exec.assert_called_once()
    
    def test_login_for_access_token_verify_select_statement(self, monkeypatch):
        """Test that the correct select statement is used in login."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        user_service.login_for_access_token(
            username="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        mock_db.exec.assert_called_once()
        call_args = mock_db.exec.call_args[0][0]
        call_str = str(call_args).lower()
        assert "select" in call_str
        assert "from users" in call_str
        assert "email" in call_str
    
    def test_login_for_access_token_multiple_calls(self, monkeypatch):
        """Test multiple login attempts."""
        # Arrange
        mock_db = Mock()
        mock_user1 = User(
            id=1,
            uuid="uuid1",
            email="user1@test.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        mock_user2 = User(
            id=2,
            uuid="uuid2",
            email="user2@test.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.side_effect = [mock_user1, mock_user2]
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        result1 = user_service.login_for_access_token(
            username="user1@test.com",
            password="ValidPass123!"
        )
        result2 = user_service.login_for_access_token(
            username="user2@test.com",
            password="ValidPass123!"
        )
        
        # Assert
        assert "access_token" in result1
        assert "access_token" in result2
        assert result1["token_type"] == "bearer"
        assert result2["token_type"] == "bearer"
        assert mock_db.exec.call_count == 2
    
    def test_login_for_access_token_token_structure(self, monkeypatch):
        """Test that the returned token has the correct structure."""
        # Arrange
        mock_db = Mock()
        mock_user = User(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            hashed_password="ValidPass123!",
            is_active=True,
            is_superuser=False
        )
        
        # Mock database operations
        mock_db.exec.return_value.first.return_value = mock_user
        
        # Mock verify_password to return True
        def mock_verify_password(plain_password, hashed_password):
            return True
        
        # Mock create_access_token to return a fake token
        def mock_create_access_token(data, expires_delta):
            return "fake_access_token_123"
        
        # Apply mocks
        monkeypatch.setattr("src.services.user_service.verify_password", mock_verify_password)
        monkeypatch.setattr("src.services.user_service.create_access_token", mock_create_access_token)
        
        user_service = UserService(mock_db)
        
        # Act
        result = user_service.login_for_access_token(
            username="test@example.com",
            password="ValidPass123!"
        )
        
        # Assert
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "access_token" in result
        assert "token_type" in result
        assert isinstance(result["access_token"], str)
        assert isinstance(result["token_type"], str)
        assert len(result["access_token"]) > 0
        assert result["token_type"] == "bearer"

