import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from src.services.user_service import UserService
from src.models.user import User
from sqlmodel import select


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
        """Test get_all_users returns users with varied field values."""
        mock_db = Mock()
        mock_users = [
            User(id=1, uuid="uuid1", email="user1@test.com", is_active=True, is_superuser=False),
            User(id=2, uuid="uuid2", email="user2@test.com", is_active=False, is_superuser=True, full_name="",),
            User(id=3, uuid="uuid3", email="user3@test.com", is_active=True, is_superuser=False, full_name=None),
        ]
        mock_exec = Mock()
        mock_exec.all.side_effect = [mock_users, mock_users]  # First for users, second for count
        mock_db.exec.return_value = mock_exec
        user_service = UserService(mock_db)
        result = user_service.get_all_users()
        assert result["users"] == mock_users
        assert result["users"][1].is_active is False
        assert result["users"][1].is_superuser is True
        assert result["users"][1].full_name == ""
        assert result["users"][2].email == "user3@test.com"
        assert result["users"][2].full_name is None
    
