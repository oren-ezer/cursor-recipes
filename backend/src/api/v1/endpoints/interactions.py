from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional, Annotated
from pydantic import BaseModel
from src.utils.dependencies import get_interaction_service
from src.services.interaction_service import InteractionService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipes", tags=["interactions"])

class RatingCreate(BaseModel):
    score: int

class CommentCreate(BaseModel):
    content: str

class CommentUpdate(BaseModel):
    content: str

class ReactionCreate(BaseModel):
    reaction_type: str

class CommentResponse(BaseModel):
    id: int
    recipe_id: int
    user_id: str
    user_full_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime
    reactions: Optional[Dict[str, Any]] = None

# ==========================
# Favorites
# ==========================
@router.post("/{recipe_id}/favorite", status_code=status.HTTP_200_OK)
async def toggle_favorite(
    recipe_id: int,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return interaction_service.toggle_favorite(recipe_id, user["uuid"])

@router.get("/me/favorites", response_model=List[int])
async def get_my_favorites(
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return interaction_service.get_user_favorites(user["uuid"], limit, offset)

# ==========================
# Ratings
# ==========================
@router.post("/{recipe_id}/rating", status_code=status.HTTP_200_OK)
async def set_rating(
    recipe_id: int,
    rating: RatingCreate,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    if rating.score < 1 or rating.score > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score must be between 1 and 5")
        
    return interaction_service.set_rating(recipe_id, user["uuid"], rating.score)

@router.delete("/{recipe_id}/rating", status_code=status.HTTP_200_OK)
async def delete_rating(
    recipe_id: int,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return interaction_service.delete_rating(recipe_id, user["uuid"])

# ==========================
# Comments
# ==========================
@router.get("/{recipe_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    recipe_id: int,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    comments = interaction_service.get_comments(recipe_id, limit, offset)
    
    user = getattr(request.state, "user", None)
    user_uuid = user.get("uuid") if user else None
    
    comment_ids = [c["id"] for c in comments]
    reactions_data = interaction_service.get_comment_reactions(comment_ids, user_uuid)
    
    response = []
    for c in comments:
        c["reactions"] = reactions_data.get(c["id"], {"counts": {}, "user_reaction": None})
        response.append(c)
        
    return response

@router.post("/{recipe_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    recipe_id: int,
    comment: CommentCreate,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    if not comment.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment cannot be empty")
        
    created_dict = interaction_service.add_comment(recipe_id, user["uuid"], comment.content)
    created_dict["reactions"] = {"counts": {}, "user_reaction": None}
    return created_dict

@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    if not comment.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment cannot be empty")
        
    updated_dict = interaction_service.update_comment(comment_id, user["uuid"], comment.content)
    if not updated_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not authorized")
        
    reactions_data = interaction_service.get_comment_reactions([comment_id], user["uuid"])
    
    updated_dict["reactions"] = reactions_data.get(comment_id, {"counts": {}, "user_reaction": None})
    return updated_dict

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    is_superuser = user.get("is_superuser", False)
    success = interaction_service.delete_comment(comment_id, user["uuid"], is_superuser)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not authorized")
    
    return None

# ==========================
# Reactions
# ==========================
@router.post("/comments/{comment_id}/reactions", status_code=status.HTTP_200_OK)
async def toggle_reaction(
    comment_id: int,
    reaction: ReactionCreate,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    return interaction_service.toggle_reaction(comment_id, user["uuid"], reaction.reaction_type)
