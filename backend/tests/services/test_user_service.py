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
    
