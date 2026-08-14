import pytest
from unittest.mock import Mock, MagicMock
from sqlmodel import Session
from src.services.interaction_service import InteractionService, InteractionMetadata
from src.models.recipe_favorite import RecipeFavorite
from src.models.recipe_rating import RecipeRating
from src.models.recipe_comment import RecipeComment
from src.models.comment_reaction import CommentReaction
from src.models.user import User

class TestInteractionService:
    def test_interaction_service_initialization(self):
        mock_db = Mock()
        service = InteractionService(mock_db)
        assert service.db == mock_db

    # ==========================
    # Favorites
    # ==========================
    def test_toggle_favorite_add(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        mock_db.add = Mock()
        mock_db.commit = Mock()

        service = InteractionService(mock_db)
        result = service.toggle_favorite(1, "user1")

        assert result == {"status": "added"}
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_toggle_favorite_remove(self):
        mock_db = Mock()
        mock_exec = Mock()
        favorite = RecipeFavorite(recipe_id=1, user_id="user1")
        mock_exec.first.return_value = favorite
        mock_db.exec.return_value = mock_exec
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        service = InteractionService(mock_db)
        result = service.toggle_favorite(1, "user1")

        assert result == {"status": "removed"}
        mock_db.delete.assert_called_once_with(favorite)
        mock_db.commit.assert_called_once()

    def test_get_user_favorites(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.all.return_value = [1, 2, 3]
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.get_user_favorites("user1", limit=10, offset=0)

        assert result == [1, 2, 3]
        mock_db.exec.assert_called_once()

    # ==========================
    # Ratings
    # ==========================
    def test_set_rating_add(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec
        mock_db.add = Mock()
        mock_db.commit = Mock()

        service = InteractionService(mock_db)
        result = service.set_rating(1, "user1", 5)

        assert result == {"status": "set", "score": 5}
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_set_rating_update(self):
        mock_db = Mock()
        mock_exec = Mock()
        rating = RecipeRating(recipe_id=1, user_id="user1", score=3)
        mock_exec.first.return_value = rating
        mock_db.exec.return_value = mock_exec
        mock_db.add = Mock()
        mock_db.commit = Mock()

        service = InteractionService(mock_db)
        result = service.set_rating(1, "user1", 5)

        assert result == {"status": "set", "score": 5}
        assert rating.score == 5
        mock_db.add.assert_called_once_with(rating)
        mock_db.commit.assert_called_once()

    def test_delete_rating_found(self):
        mock_db = Mock()
        mock_exec = Mock()
        rating = RecipeRating(recipe_id=1, user_id="user1", score=5)
        mock_exec.first.return_value = rating
        mock_db.exec.return_value = mock_exec
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        service = InteractionService(mock_db)
        result = service.delete_rating(1, "user1")

        assert result == {"status": "deleted"}
        mock_db.delete.assert_called_once_with(rating)
        mock_db.commit.assert_called_once()

    def test_delete_rating_not_found(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.delete_rating(1, "user1")

        assert result == {"status": "not_found"}

    # ==========================
    # Comments
    # ==========================
    def test_get_comments(self):
        mock_db = Mock()
        mock_exec = Mock()
        
        # We need mock comment and user
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Great!")
        user = User(uuid="user1", email="test@test.com", full_name="Test User", hashed_password="pw")
        
        mock_exec.all.return_value = [(comment, user)]
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.get_comments(1)

        assert len(result) == 1
        assert result[0]["content"] == "Great!"
        assert result[0]["user_full_name"] == "Test User"
        
    def test_get_comments_no_full_name(self):
        mock_db = Mock()
        mock_exec = Mock()
        
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Great!")
        user = User(uuid="user1", email="test@test.com", hashed_password="pw") # No full name
        
        mock_exec.all.return_value = [(comment, user)]
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.get_comments(1)

        assert result[0]["user_full_name"] == "test" # Splits from email

    def test_add_comment(self):
        mock_db = Mock()
        user = User(uuid="user1", email="test@test.com", full_name="Test User", hashed_password="pw")
        
        mock_exec = Mock()
        mock_exec.first.return_value = user
        mock_db.exec.return_value = mock_exec
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        service = InteractionService(mock_db)
        result = service.add_comment(1, "user1", "Nice")

        assert result["content"] == "Nice"
        assert result["user_full_name"] == "Test User"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
    def test_add_comment_no_user(self):
        mock_db = Mock()
        
        mock_exec = Mock()
        mock_exec.first.return_value = None # User not found
        mock_db.exec.return_value = mock_exec
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        service = InteractionService(mock_db)
        result = service.add_comment(1, "user1", "Nice")

        assert result["user_full_name"] == "User"

    def test_add_comment_no_full_name(self):
        mock_db = Mock()
        user = User(uuid="user1", email="test@test.com", hashed_password="pw")
        
        mock_exec = Mock()
        mock_exec.first.return_value = user
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.add_comment(1, "user1", "Nice")

        assert result["user_full_name"] == "test"

    def test_update_comment_found(self):
        mock_db = Mock()
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Old")
        user = User(uuid="user1", email="test@test.com", full_name="Test User", hashed_password="pw")
        
        mock_exec_comment = Mock()
        mock_exec_comment.first.return_value = comment
        mock_exec_user = Mock()
        mock_exec_user.first.return_value = user
        
        mock_db.exec.side_effect = [mock_exec_comment, mock_exec_user]
        
        service = InteractionService(mock_db)
        result = service.update_comment(1, "user1", "New")

        assert result["content"] == "New"
        assert result["user_full_name"] == "Test User"
        assert comment.content == "New"

    def test_update_comment_no_user_for_fullname(self):
        mock_db = Mock()
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Old")
        
        mock_exec_comment = Mock()
        mock_exec_comment.first.return_value = comment
        mock_exec_user = Mock()
        mock_exec_user.first.return_value = None
        
        mock_db.exec.side_effect = [mock_exec_comment, mock_exec_user]
        
        service = InteractionService(mock_db)
        result = service.update_comment(1, "user1", "New")

        assert result["user_full_name"] == "User"

    def test_update_comment_user_no_fullname(self):
        mock_db = Mock()
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Old")
        user = User(uuid="user1", email="test@test.com", hashed_password="pw")
        
        mock_exec_comment = Mock()
        mock_exec_comment.first.return_value = comment
        mock_exec_user = Mock()
        mock_exec_user.first.return_value = user
        
        mock_db.exec.side_effect = [mock_exec_comment, mock_exec_user]
        
        service = InteractionService(mock_db)
        result = service.update_comment(1, "user1", "New")

        assert result["user_full_name"] == "test"

    def test_update_comment_not_found(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.update_comment(1, "user1", "New")

        assert result is None

    def test_delete_comment_owner(self):
        mock_db = Mock()
        comment = RecipeComment(id=1, recipe_id=1, user_id="user1", content="Old")
        mock_exec = Mock()
        mock_exec.first.return_value = comment
        mock_db.exec.return_value = mock_exec
        mock_db.delete = Mock()

        service = InteractionService(mock_db)
        result = service.delete_comment(1, "user1")

        assert result is True
        mock_db.delete.assert_called_once_with(comment)

    def test_delete_comment_superuser(self):
        mock_db = Mock()
        comment = RecipeComment(id=1, recipe_id=1, user_id="other_user", content="Old")
        mock_exec = Mock()
        mock_exec.first.return_value = comment
        mock_db.exec.return_value = mock_exec
        mock_db.delete = Mock()

        service = InteractionService(mock_db)
        result = service.delete_comment(1, "admin", is_superuser=True)

        assert result is True
        mock_db.delete.assert_called_once_with(comment)

    def test_delete_comment_not_found(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.delete_comment(1, "user1")

        assert result is False

    # ==========================
    # Reactions
    # ==========================
    def test_toggle_reaction_add(self):
        mock_db = Mock()
        mock_exec = Mock()
        mock_exec.first.return_value = None
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.toggle_reaction(1, "user1", "like")

        assert result == {"status": "added", "reaction_type": "like"}

    def test_toggle_reaction_remove(self):
        mock_db = Mock()
        reaction = CommentReaction(comment_id=1, user_id="user1", reaction_type="like")
        mock_exec = Mock()
        mock_exec.first.return_value = reaction
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.toggle_reaction(1, "user1", "like")

        assert result == {"status": "removed"}

    def test_toggle_reaction_update(self):
        mock_db = Mock()
        reaction = CommentReaction(comment_id=1, user_id="user1", reaction_type="like")
        mock_exec = Mock()
        mock_exec.first.return_value = reaction
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.toggle_reaction(1, "user1", "love")

        assert result == {"status": "updated", "reaction_type": "love"}
        assert reaction.reaction_type == "love"

    def test_get_comment_reactions_empty(self):
        mock_db = Mock()
        service = InteractionService(mock_db)
        result = service.get_comment_reactions([])
        assert result == {}

    def test_get_comment_reactions(self):
        mock_db = Mock()
        r1 = CommentReaction(comment_id=1, user_id="user1", reaction_type="like")
        r2 = CommentReaction(comment_id=1, user_id="user2", reaction_type="like")
        r3 = CommentReaction(comment_id=1, user_id="user3", reaction_type="love")
        r4 = CommentReaction(comment_id=2, user_id="user1", reaction_type="love")
        
        mock_exec = Mock()
        mock_exec.all.return_value = [r1, r2, r3, r4]
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.get_comment_reactions([1, 2], current_user_id="user1")

        assert result[1]["counts"]["like"] == 2
        assert result[1]["counts"]["love"] == 1
        assert result[1]["user_reaction"] == "like"
        
        assert result[2]["counts"]["love"] == 1
        assert result[2]["user_reaction"] == "love"
        
    def test_get_comment_reactions_no_current_user(self):
        mock_db = Mock()
        r1 = CommentReaction(comment_id=1, user_id="user1", reaction_type="like")
        
        mock_exec = Mock()
        mock_exec.all.return_value = [r1]
        mock_db.exec.return_value = mock_exec

        service = InteractionService(mock_db)
        result = service.get_comment_reactions([1])

        assert result[1]["counts"]["like"] == 1
        assert result[1]["user_reaction"] is None

    # ==========================
    # Metadata Aggregation
    # ==========================
    def test_get_recipes_metadata_empty(self):
        mock_db = Mock()
        service = InteractionService(mock_db)
        assert service.get_recipes_metadata([]) == {}

    def test_get_recipes_metadata(self):
        mock_db = Mock()
        
        # 1. fav_stmt
        mock_exec_fav = Mock()
        mock_exec_fav.all.return_value = [(1, 5), (2, 2)]
        
        # 2. rating_stmt
        mock_exec_rating = Mock()
        mock_exec_rating.all.return_value = [(1, 4.5, 10), (2, None, 0)]
        
        # 3. comments_stmt
        mock_exec_comments = Mock()
        mock_exec_comments.all.return_value = [(1, 3)]
        
        # 4. user_fav_stmt
        mock_exec_user_fav = Mock()
        mock_exec_user_fav.all.return_value = [1]
        
        # 5. user_rating_stmt
        mock_exec_user_rating = Mock()
        mock_exec_user_rating.all.return_value = [(1, 5)]
        
        mock_db.exec.side_effect = [
            mock_exec_fav,
            mock_exec_rating,
            mock_exec_comments,
            mock_exec_user_fav,
            mock_exec_user_rating
        ]

        service = InteractionService(mock_db)
        result = service.get_recipes_metadata([1, 2], current_user_id="user1")

        assert result[1].favorites_count == 5
        assert result[1].average_rating == 4.5
        assert result[1].ratings_count == 10
        assert result[1].comments_count == 3
        assert result[1].is_favorited is True
        assert result[1].user_rating == 5
        
        assert result[2].favorites_count == 2
        assert result[2].average_rating == 0.0
        assert result[2].ratings_count == 0
        assert result[2].comments_count == 0
        assert result[2].is_favorited is False
        assert result[2].user_rating is None
