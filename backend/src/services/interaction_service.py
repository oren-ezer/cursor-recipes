from sqlalchemy.orm import Session
from sqlmodel import select, func
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from src.models.recipe_favorite import RecipeFavorite
from src.models.recipe_rating import RecipeRating
from src.models.recipe_comment import RecipeComment
from src.models.comment_reaction import CommentReaction
from src.models.user import User

class InteractionMetadata(BaseModel):
    favorites_count: int = 0
    is_favorited: bool = False
    average_rating: float = 0.0
    ratings_count: int = 0
    user_rating: Optional[int] = None
    comments_count: int = 0

class InteractionService:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # Favorites
    # ==========================
    def toggle_favorite(self, recipe_id: int, user_id: str) -> dict:
        statement = select(RecipeFavorite).where(
            RecipeFavorite.recipe_id == recipe_id, 
            RecipeFavorite.user_id == user_id
        )
        favorite = self.db.exec(statement).first()
        
        if favorite:
            self.db.delete(favorite)
            self.db.commit()
            return {"status": "removed"}
        else:
            new_favorite = RecipeFavorite(recipe_id=recipe_id, user_id=user_id)
            self.db.add(new_favorite)
            self.db.commit()
            return {"status": "added"}

    def get_user_favorites(self, user_id: str, limit: int = 100, offset: int = 0) -> List[int]:
        statement = select(RecipeFavorite.recipe_id).where(
            RecipeFavorite.user_id == user_id
        ).offset(offset).limit(limit)
        return list(self.db.exec(statement).all())

    # ==========================
    # Ratings
    # ==========================
    def set_rating(self, recipe_id: int, user_id: str, score: int) -> dict:
        statement = select(RecipeRating).where(
            RecipeRating.recipe_id == recipe_id, 
            RecipeRating.user_id == user_id
        )
        rating = self.db.exec(statement).first()
        
        if rating:
            rating.score = score
            self.db.add(rating)
        else:
            rating = RecipeRating(recipe_id=recipe_id, user_id=user_id, score=score)
            self.db.add(rating)
            
        self.db.commit()
        return {"status": "set", "score": score}

    def delete_rating(self, recipe_id: int, user_id: str) -> dict:
        statement = select(RecipeRating).where(
            RecipeRating.recipe_id == recipe_id, 
            RecipeRating.user_id == user_id
        )
        rating = self.db.exec(statement).first()
        if rating:
            self.db.delete(rating)
            self.db.commit()
            return {"status": "deleted"}
        return {"status": "not_found"}

    # ==========================
    # Comments
    # ==========================
    def get_comments(self, recipe_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        statement = select(RecipeComment, User).join(
            User, RecipeComment.user_id == User.uuid
        ).where(
            RecipeComment.recipe_id == recipe_id
        ).order_by(RecipeComment.created_at.desc()).offset(offset).limit(limit)
        
        results = self.db.exec(statement).all()
        comments_with_user = []
        for comment, user in results:
            c_dict = comment.model_dump()
            c_dict["user_full_name"] = user.full_name or user.email.split('@')[0]
            comments_with_user.append(c_dict)
            
        return comments_with_user

    def add_comment(self, recipe_id: int, user_id: str, content: str) -> Dict[str, Any]:
        comment = RecipeComment(recipe_id=recipe_id, user_id=user_id, content=content)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        # Get user for full name
        user_stmt = select(User).where(User.uuid == user_id)
        user = self.db.exec(user_stmt).first()
        
        c_dict = comment.model_dump()
        c_dict["user_full_name"] = user.full_name or user.email.split('@')[0] if user else "User"
        return c_dict

    def update_comment(self, comment_id: int, user_id: str, content: str) -> Optional[Dict[str, Any]]:
        statement = select(RecipeComment).where(
            RecipeComment.id == comment_id,
            RecipeComment.user_id == user_id
        )
        comment = self.db.exec(statement).first()
        if comment:
            comment.content = content
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            
            # Get user for full name
            user_stmt = select(User).where(User.uuid == user_id)
            user = self.db.exec(user_stmt).first()
            
            c_dict = comment.model_dump()
            c_dict["user_full_name"] = user.full_name or user.email.split('@')[0] if user else "User"
            return c_dict
        return None

    def delete_comment(self, comment_id: int, user_id: str, is_superuser: bool = False) -> bool:
        statement = select(RecipeComment).where(RecipeComment.id == comment_id)
        if not is_superuser:
            statement = statement.where(RecipeComment.user_id == user_id)
            
        comment = self.db.exec(statement).first()
        if comment:
            self.db.delete(comment)
            self.db.commit()
            return True
        return False

    # ==========================
    # Reactions
    # ==========================
    def toggle_reaction(self, comment_id: int, user_id: str, reaction_type: str) -> dict:
        statement = select(CommentReaction).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == user_id
        )
        reaction = self.db.exec(statement).first()
        
        if reaction:
            if reaction.reaction_type == reaction_type:
                self.db.delete(reaction)
                self.db.commit()
                return {"status": "removed"}
            else:
                reaction.reaction_type = reaction_type
                self.db.add(reaction)
                self.db.commit()
                return {"status": "updated", "reaction_type": reaction_type}
        else:
            new_reaction = CommentReaction(comment_id=comment_id, user_id=user_id, reaction_type=reaction_type)
            self.db.add(new_reaction)
            self.db.commit()
            return {"status": "added", "reaction_type": reaction_type}

    def get_comment_reactions(self, comment_ids: List[int], current_user_id: Optional[str] = None) -> Dict[int, dict]:
        """
        Returns a dict of comment_id -> reaction summary (counts by type, and user's reaction).
        """
        if not comment_ids:
            return {}
            
        # Get all reactions for these comments
        statement = select(CommentReaction).where(CommentReaction.comment_id.in_(comment_ids))
        reactions = self.db.exec(statement).all()
        
        result = {cid: {"counts": {}, "user_reaction": None} for cid in comment_ids}
        
        for r in reactions:
            if r.reaction_type not in result[r.comment_id]["counts"]:
                result[r.comment_id]["counts"][r.reaction_type] = 0
            result[r.comment_id]["counts"][r.reaction_type] += 1
            
            if current_user_id and r.user_id == current_user_id:
                result[r.comment_id]["user_reaction"] = r.reaction_type
                
        return result

    # ==========================
    # Metadata Aggregation
    # ==========================
    def get_recipes_metadata(self, recipe_ids: List[int], current_user_id: Optional[str] = None) -> Dict[int, InteractionMetadata]:
        if not recipe_ids:
            return {}

        # Initialize default metadata
        metadata = {rid: InteractionMetadata() for rid in recipe_ids}

        # Favorites count
        fav_stmt = select(RecipeFavorite.recipe_id, func.count(RecipeFavorite.id)).where(
            RecipeFavorite.recipe_id.in_(recipe_ids)
        ).group_by(RecipeFavorite.recipe_id)
        for rid, count in self.db.exec(fav_stmt).all():
            metadata[rid].favorites_count = count

        # Ratings avg and count
        rating_stmt = select(
            RecipeRating.recipe_id, 
            func.avg(RecipeRating.score),
            func.count(RecipeRating.id)
        ).where(
            RecipeRating.recipe_id.in_(recipe_ids)
        ).group_by(RecipeRating.recipe_id)
        for rid, avg, count in self.db.exec(rating_stmt).all():
            metadata[rid].average_rating = float(avg) if avg else 0.0
            metadata[rid].ratings_count = count

        # Comments count
        comments_stmt = select(RecipeComment.recipe_id, func.count(RecipeComment.id)).where(
            RecipeComment.recipe_id.in_(recipe_ids)
        ).group_by(RecipeComment.recipe_id)
        for rid, count in self.db.exec(comments_stmt).all():
            metadata[rid].comments_count = count

        # Current user specific data
        if current_user_id:
            # User favorites
            user_fav_stmt = select(RecipeFavorite.recipe_id).where(
                RecipeFavorite.recipe_id.in_(recipe_ids),
                RecipeFavorite.user_id == current_user_id
            )
            for rid in self.db.exec(user_fav_stmt).all():
                metadata[rid].is_favorited = True

            # User ratings
            user_rating_stmt = select(RecipeRating.recipe_id, RecipeRating.score).where(
                RecipeRating.recipe_id.in_(recipe_ids),
                RecipeRating.user_id == current_user_id
            )
            for rid, score in self.db.exec(user_rating_stmt).all():
                metadata[rid].user_rating = score

        return metadata
