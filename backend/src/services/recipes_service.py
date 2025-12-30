from sqlmodel import select
from sqlalchemy.orm import Session
from src.models.recipe import Recipe
from src.models.tag import Tag
from src.models.recipe_tag import RecipeTag
from src.services.tag_service import TagService
from datetime import datetime


class RecipeService:
    """Service class for recipe-related operations."""
    
    def __init__(self, db: Session, tag_service: TagService = None):
        self.db = db
        self.tag_service = tag_service
    
    def get_recipe(self, recipe_id: int) -> Recipe | None:
        """
        Get a recipe by ID.
        
        Args:
            recipe_id: The ID of the recipe to retrieve
            
        Returns:
            Recipe object if found, None otherwise
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        return self.db.execute(statement).scalars().first()

    def _add_tags_to_recipe_dict(self, recipe: Recipe) -> dict:
        """
        Helper method to add tags to a recipe dictionary.
        
        Args:
            recipe: Recipe object to convert to dict with tags
            
        Returns:
            Dictionary with recipe data and tags
        """
        recipe_dict = recipe.model_dump()
        
        # Get tags if tag_service is available
        tags = []
        if self.tag_service:
            tags = self.tag_service.get_tags_for_recipe(recipe.id)
        
        recipe_dict["tags"] = [
            {"id": tag.id, "name": tag.name, "category": tag.category}
            for tag in tags
        ]
        
        return recipe_dict

    def get_recipe_with_tags(self, recipe_id: int) -> dict | None:
        """
        Get a recipe by ID with its tags.
        
        Args:
            recipe_id: The ID of the recipe to retrieve
            
        Returns:
            Dictionary with recipe data and tags, None if recipe not found
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        
        return self._add_tags_to_recipe_dict(recipe)
    
    def get_all_my_recipes(self, limit: int = 100, offset: int = 0, user_id: str = None) -> dict:
        """
        Get all recipes with pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            user_id: Optional user ID to filter recipes by user
            
        Returns:
            Dictionary with recipes, total count, limit, and offset
        """
        # Build base statement
        statement = select(Recipe)
        count_statement = select(Recipe)
        
        # Add user filter if provided
        if user_id:
            statement = statement.where(Recipe.user_id == user_id)
            count_statement = count_statement.where(Recipe.user_id == user_id)
        
        # Add pagination
        statement = statement.offset(offset).limit(limit)
        
        # Get recipes for current page
        recipes = self.db.execute(statement).scalars().all()
        
        # Get total count
        total = len(self.db.execute(count_statement).scalars().all())
        
        return {
            "recipes": recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def get_all_my_recipes_with_tags(self, limit: int = 100, offset: int = 0, user_id: str = None) -> dict:
        """
        Get all recipes with tags and pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            user_id: Optional user ID to filter recipes by user
            
        Returns:
            Dictionary with recipes (including tags), total count, limit, and offset
        """
        # Get base recipes
        result = self.get_all_my_recipes(limit, offset, user_id)
        
        # Add tags to each recipe if tag_service is available
        if self.tag_service:
            recipes_with_tags = []
            for recipe in result["recipes"]:
                recipes_with_tags.append(self._add_tags_to_recipe_dict(recipe))
            result["recipes"] = recipes_with_tags
        
        return result
    
    def get_all_public_recipes(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get only public recipes with pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with public recipes, total count, limit, and offset
        """
        # Build base statement for public recipes only
        statement = select(Recipe).where(Recipe.is_public == True)
        count_statement = select(Recipe).where(Recipe.is_public == True)
        
        # Add pagination
        statement = statement.offset(offset).limit(limit)
        
        # Get recipes for current page
        recipes = self.db.execute(statement).scalars().all()
        
        # Get total count
        total = len(self.db.execute(count_statement).scalars().all())
        
        return {
            "recipes": recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def get_all_public_recipes_with_tags(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get only public recipes with tags and pagination support using limit/offset.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with public recipes (including tags), total count, limit, and offset
        """
        # Get base recipes
        result = self.get_all_public_recipes(limit, offset)
        
        # Add tags to each recipe if tag_service is available
        if self.tag_service:
            recipes_with_tags = []
            for recipe in result["recipes"]:
                recipes_with_tags.append(self._add_tags_to_recipe_dict(recipe))
            result["recipes"] = recipes_with_tags
        
        return result
    
    def get_all_recipes_with_tags(self, limit: int = 100, offset: int = 0) -> dict:
        """
        Get ALL recipes (public and private) with tags and pagination support.
        This method is intended for admin use only.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Dictionary with all recipes (including tags), total count, limit, and offset
        """
        # Build statement for ALL recipes (no public filter)
        statement = select(Recipe)
        count_statement = select(Recipe)
        
        # Add pagination
        statement = statement.offset(offset).limit(limit)
        
        # Get recipes for current page
        recipes = self.db.execute(statement).scalars().all()
        
        # Get total count
        total = len(self.db.execute(count_statement).scalars().all())
        
        result = {
            "recipes": recipes,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
        # Add tags to each recipe if tag_service is available
        if self.tag_service:
            recipes_with_tags = []
            for recipe in result["recipes"]:
                recipes_with_tags.append(self._add_tags_to_recipe_dict(recipe))
            result["recipes"] = recipes_with_tags
        
        return result
    
    def create_recipe(self, recipe_data: dict, user_uuid: str) -> Recipe:
        """
        Create a new recipe.
        
        Args:
            recipe_data: Dictionary containing recipe data
            user_uuid: UUID of the user creating the recipe
            
        Returns:
            Created Recipe object
            
        Raises:
            ValueError: If validation fails
        """
        recipe_data["user_id"] = user_uuid
        recipe = Recipe(**recipe_data)
        self.db.add(recipe)
        self.db.flush()
        self.db.commit()  # Commit the transaction to persist the recipe
        self.db.refresh(recipe)
        return recipe

    def create_recipe_with_tags(self, recipe_data: dict, user_uuid: str) -> dict:
        """
        Create a new recipe with tags.
        
        Args:
            recipe_data: Dictionary containing recipe data
            user_uuid: UUID of the user creating the recipe
            
        Returns:
            Dictionary with created recipe data and tags
            
        Raises:
            ValueError: If validation fails
        """
        # Extract tag_ids for later processing
        tag_ids = recipe_data.pop("tag_ids", None)
        
        # Create the recipe
        created_recipe = self.create_recipe(recipe_data, user_uuid)
        
        # Add tags to the recipe if provided
        if tag_ids and self.tag_service:
            tag_result = self.tag_service.update_recipe_tags(
                recipe_id=created_recipe.id,
                add_tag_ids=tag_ids
            )
            if tag_result["errors"]:
                # Fail the creation if there are errors
                raise ValueError(f"Failed to add tags to recipe: {tag_result['errors']}")
            if tag_result["warnings"]:
                # Log warnings but don't fail the creation
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Some warnings when adding tags to recipe {created_recipe.id}: {tag_result['warnings']}")
        
        # Return recipe with tags
        return self.get_recipe_with_tags(created_recipe.id)
    
    def update_recipe(self, recipe_id: int, update_data: dict, user_uuid: str, is_superuser: bool = False) -> Recipe:
        """
        Update a recipe.
        
        Args:
            recipe_id: The ID of the recipe to update
            update_data: Dictionary containing the fields to update
            user_uuid: UUID of the user updating the recipe
            is_superuser: Whether the user is a superuser/admin (can edit any recipe)
            
        Returns:
            Updated Recipe object
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        recipe = self.db.execute(statement).scalars().first()
        
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        # Allow superusers to update any recipe
        if recipe.user_id != user_uuid and not is_superuser:
            raise ValueError("Not authorized to update this recipe")
        
        if not update_data:
            return recipe
        
        # Handle ingredients conversion if needed
        if "ingredients" in update_data and update_data["ingredients"] is not None:
            if hasattr(update_data["ingredients"][0], 'model_dump'):
                update_data["ingredients"] = [ingredient.model_dump() for ingredient in update_data["ingredients"]]
        
        # Update fields
        for field, value in update_data.items():
            if value is not None and hasattr(recipe, field):
                setattr(recipe, field, value)
        
        # Update timestamp
        recipe.updated_at = datetime.now()
        
        self.db.flush()
        self.db.commit()  # Commit the transaction to persist changes
        self.db.refresh(recipe)
        return recipe

    def update_recipe_with_tags(self, recipe_id: int, update_data: dict, user_uuid: str, is_superuser: bool = False) -> dict:
        """
        Update a recipe with tags.
        
        Args:
            recipe_id: The ID of the recipe to update
            update_data: Dictionary containing the fields to update
            user_uuid: UUID of the user updating the recipe
            is_superuser: Whether the user is a superuser/admin (can edit any recipe)
            
        Returns:
            Dictionary with updated recipe data and tags
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        # Extract tag_ids for later processing
        tag_ids = update_data.pop("tag_ids", None)
        
        # Update the recipe
        updated_recipe = self.update_recipe(recipe_id, update_data, user_uuid, is_superuser)
        
        # Update tags if provided
        if tag_ids is not None and self.tag_service:
            # Get current tags to determine what to remove
            current_tags = self.tag_service.get_tags_for_recipe(recipe_id)
            current_tag_ids = [tag.id for tag in current_tags]
            
            # Calculate what to add and remove
            tags_to_add = [tid for tid in tag_ids if tid not in current_tag_ids]
            tags_to_remove = [tid for tid in current_tag_ids if tid not in tag_ids]
            
            if tags_to_add or tags_to_remove:
                tag_result = self.tag_service.update_recipe_tags(
                    recipe_id=recipe_id,
                    add_tag_ids=tags_to_add,
                    remove_tag_ids=tags_to_remove
                )
                if tag_result["errors"]:
                    # Fail the update if there are errors
                    raise ValueError(f"Failed to update tags for recipe: {tag_result['errors']}")
                if tag_result["warnings"]:
                    # Log warnings but don't fail the update
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Some warnings when updating tags for recipe {recipe_id}: {tag_result['warnings']}")
        
        # Return recipe with tags
        return self.get_recipe_with_tags(recipe_id)
    
    def delete_recipe(self, recipe_id: int, user_uuid: str, is_superuser: bool = False) -> None:
        """
        Delete a recipe.
        
        Args:
            recipe_id: The ID of the recipe to delete
            user_uuid: UUID of the user deleting the recipe
            is_superuser: Whether the user is a superuser/admin (can delete any recipe)
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        statement = select(Recipe).where(Recipe.id == recipe_id)
        recipe = self.db.execute(statement).scalars().first()
        
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        # Allow superusers to delete any recipe
        if recipe.user_id != user_uuid and not is_superuser:
            raise ValueError("Not authorized to delete this recipe")
        
        self.db.delete(recipe)
        self.db.flush()
        self.db.commit()  # Commit the transaction to persist deletion

    def delete_recipe_with_tags(self, recipe_id: int, user_uuid: str, is_superuser: bool = False) -> None:
        """
        Delete a recipe and remove all its tag associations.
        
        Args:
            recipe_id: The ID of the recipe to delete
            user_uuid: UUID of the user deleting the recipe
            is_superuser: Whether the user is a superuser/admin (can delete any recipe)
            
        Raises:
            ValueError: If recipe not found or user not authorized
        """
        # First remove all tag associations if tag_service is available
        if self.tag_service:
            current_tags = self.tag_service.get_tags_for_recipe(recipe_id)
            if current_tags:
                current_tag_ids = [tag.id for tag in current_tags]
                self.tag_service.update_recipe_tags(
                    recipe_id=recipe_id,
                    remove_tag_ids=current_tag_ids
                )
        
        # Then delete the recipe
        self.delete_recipe(recipe_id, user_uuid, is_superuser)

    def export_recipe_to_json(self, recipe_id: int) -> dict:
        """
        Export a recipe to JSON format.
        
        Args:
            recipe_id: The ID of the recipe to export
            
        Returns:
            Dictionary representation of the recipe with all details
            
        Raises:
            ValueError: If recipe not found
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        return self._add_tags_to_recipe_dict(recipe)

    def export_recipe_to_pdf(self, recipe_id: int) -> bytes:
        """
        Export a recipe to PDF format.
        
        Args:
            recipe_id: The ID of the recipe to export
            
        Returns:
            PDF file content as bytes
            
        Raises:
            ValueError: If recipe not found
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from io import BytesIO
        from xml.sax.saxutils import escape
        
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with ID {recipe_id} not found")
        
        # Get recipe with tags
        recipe_dict = self._add_tags_to_recipe_dict(recipe)
        
        # Helper function to escape XML special characters
        def escape_text(text):
            """Escape special XML characters for ReportLab Paragraph."""
            if not text:
                return ""
            return escape(str(text), entities={
                "'": "&apos;",
                '"': "&quot;",
            })
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                              topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=6,
            spaceBefore=12,
        )
        
        # Title
        story.append(Paragraph(escape_text(recipe.title), title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Description
        if recipe.description:
            story.append(Paragraph(escape_text(recipe.description), styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Recipe Information Table
        info_data = [
            ['Preparation Time', f"{recipe.preparation_time} minutes"],
            ['Cooking Time', f"{recipe.cooking_time} minutes"],
            ['Servings', str(recipe.servings)],
            ['Difficulty', escape_text(recipe.difficulty_level)],
        ]
        
        if recipe_dict.get('tags'):
            tags_text = ', '.join([escape_text(tag['name']) for tag in recipe_dict['tags']])
            info_data.append(['Tags', tags_text])
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ingredients
        story.append(Paragraph('Ingredients', heading_style))
        for ingredient in recipe.ingredients:
            amount = escape_text(ingredient.get('amount', ''))
            name = escape_text(ingredient.get('name', ''))
            bullet_text = f"• {amount} {name}"
            story.append(Paragraph(bullet_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Instructions
        story.append(Paragraph('Instructions', heading_style))
        for i, instruction in enumerate(recipe.instructions, 1):
            escaped_instruction = escape_text(instruction)
            step_text = f"<b>Step {i}:</b> {escaped_instruction}"
            story.append(Paragraph(step_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content - seek to beginning first to ensure we read everything
        buffer.seek(0)
        pdf_content = buffer.read()
        buffer.close()
        
        return pdf_content 