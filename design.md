Design Specifications: Recipe Website
1. Overview
* **Project Name:** Recipes
* **Description:** A web application that allows users to store, manage, and share food recipes.  It supports multiple users with private and shared recipe capabilities.
* **Goal:** To provide a user-friendly platform for organizing and accessing personal recipe collections, while also enabling recipe sharing within a community or selected users.


2. Functional Requirements
* **User Authentication and Management:**
    * User registration (email, password).
    * User login and logout.
    * Password reset functionality.
    * User profile management (ability to update profile information).
    * Role-Based Access Control (RBAC):
        * Regular user: Can create, edit, and delete their own recipes. Can view shared recipes. Can share recipes with selected users.
* **Recipe Management:**
    * Create new recipes:
        * Recipe title.
        * Description.
        * Ingredients (list with quantities).
        * Instructions (step-by-step).
        * Tags/Categories (e.g., "Breakfast," "Dinner," "Dessert," "Vegan").
        * Preparation time.
        * Cooking time.
        * Servings.
        * Image upload.
        * Source (optional, e.g., URL of original recipe).
    * Edit existing recipes (only by the creator).
    * Delete recipes (only by the creator).
    * View recipe details.
    * Search recipes (by title, ingredients, tags).
    * Browse recipes.
    * Tag filtering
* **Recipe Sharing:**
    * Recipes can be private (visible only to the creator) or shared (visible to other users).
    * Shared recipes are visible to all registered users or a list of specifically selected users.
* **Data separation:**
     * Each user has their own set of private recipes created by him.
     * A separate section or database table stores the public recipes, accessible to all users.
     * Recipes shared with a specific list of users are stored in the creator’s recipes’ table, accessible to the users selected by him to share with them .

* **Favorites (Optional):**
    * Users can mark recipes as favorites for quick access.
* **Ratings (Optional):**
    * Users can rate recipes.
    * Average rating is displayed for each recipe.
* **Comments (Optional):**
    * Users can add comments to shared recipes.
* **Shopping List (Optional):**
    * Users can add ingredients from recipes to a shopping list.


3. Non-Functional Requirements
* **Performance:**
    * Fast page load times.
    * Efficient database queries.
    * Scalable to handle a growing number of users and recipes.
* **Security:**
    * Secure user authentication and authorization.
    * Protection against common web vulnerabilities (e.g., XSS, CSRF, SQL injection, etc.).
    * Secure storage of user data and recipes.
* **Usability:**
    * Intuitive and user-friendly interface.
    * Easy navigation.
    * Responsive design (works well on desktop and mobile devices).
* **Maintainability:**
    * Clean, well-organized code.
    * Easy to update and extend.
    * Comprehensive documentation.
* **Accessibility:**
     * Follows web accessibility guidelines (WCAG).
* **Internationalization:**
     * Should support multiple languages including RTL languages like Hebrew.


4. Technical Design
* **4.1 Architecture**
    * **Multi-tier architecture:**
        * Frontend (Presentation Layer): React
        * Backend (Application/Business Logic Layer): FastAPI
        * Database (Data Persistence Layer): Supabase (PostgreSQL)
    * **RESTful API:** The frontend will communicate with the backend using a RESTful API.

* **4.2 Backend (FastAPI)**
    * **Language:** Python 3.9+
    * **Framework:** FastAPI
    * **ORM:** SQLModel (built on top of SQLAlchemy)
    * **Database:** PostgreSQL (via Supabase)
    * **Authentication:**
        * JWT (JSON Web Tokens) for authentication.
        * OAuth2 for social login (optional, e.g., Google, Facebook).
    * **Data Validation:** Pydantic models for request and response data validation.
    * **Database Migrations:** Alembic for managing database schema migrations.
    * **File Storage:** Supabase Storage for storing recipe images.
    * **API Documentation:** Automatic generation of API documentation using Swagger/OpenAPI.
    * **Error Handling:** Consistent and informative error responses.
    * **CORS:** Configuration to allow cross-origin requests from the frontend.
* **4.3 Frontend (React)**
    * **Language:** TypeScript
    * **Framework:** React
    * **UI Library:** shadcn/ui
    * **Styling:** Tailwind CSS
    * **State Management:** React Context, or a library like Zustand or React Query
    * **Routing:** React Router
    * **HTTP Client:** `fetch` or `axios`
    * **Component Structure:**
        * Reusable components for UI elements (buttons, forms, cards, etc.).
        * Page components for different views (home page, recipe list, recipe detail, user profile, etc.).

* **4.4 Database (Supabase)**
    * **Database:** PostgreSQL
    * **Hosting:** Supabase
    * **Data Modeling:**
        * Tables:
            * `users`: Stores user information (id, email, password, profile details, etc.).
            * `recipes`: Stores recipe data (id, user_id, title, description, ingredients, instructions, tags, prep_time, cook_time, servings, image_url, is_shared, created_at, updated_at).
            * `shared_recipes`: Stores recipes that are shared (id, recipe_id).
            * `tags`: Stores available tags/categories (id, name).
            * `recipe_tags`:  Many-to-many relationship between recipes and tags (recipe_id, tag_id).
            * `favorites` (optional):  Stores user's favorite recipes (user_id, recipe_id).
            * `ratings` (optional): Stores user ratings for recipes (user_id, recipe_id, rating).
            * `comments` (optional): Stores comments on recipes (id, user_id, recipe_id, text, created_at).
        * Relationships:
            * `recipes` has a foreign key `user_id` referencing `users`.
            * `recipes` has a many-to-many relationship with `tags` through the `recipes_tags` table.
            * `recipes` has a many-to-many relationship with `users` through the `recipes_users` table.
            * `favorites` has foreign keys `user_id` and `recipe_id` referencing `users` and `recipes`.
            * `ratings` has foreign keys `user_id` and `recipe_id` referencing `users` and `recipes`.
            * `comments` has foreign keys `user_id` and `recipe_id` referencing `users` and `recipes`.
    * **Supabase Features:**
        * Authentication:  Use Supabase's built-in authentication for user management.
        * Storage:  Use Supabase Storage for storing recipe images.
        * Realtime (Optional):  For features like live updates to shared recipes or comments.

* **4.5 API Endpoints**
    * **User API:**
        * `POST /users/register`: Register a new user.
        * `POST /users/login`: Log in a user and return a JWT.
        * `POST /users/logout`: Log out a user (invalidate JWT on client-side).
        * `GET /users/me`: Get the current user's profile.
        * `PUT /users/me`: Update the current user's profile.
    * **Recipe API:**
        * `GET /recipes`: Get all recipes (with optional filters/pagination).
        * `GET /recipes/{recipe_id}`: Get a specific recipe.
        * `POST /recipes`: Create a new recipe (requires authentication).
        * `PUT /recipes/{recipe_id}`: Update a recipe (requires authentication, only creator).
        * `DELETE /recipes/{recipe_id}`: Delete a recipe (requires authentication, only creator).
        * `GET /users/{user_id}/recipes`: Get all recipes for a specific user (with optional additional filters/pagination).
    * **Shared Recipe API:**
        * `GET /shared_recipes`: Get all shared recipes (with optional filters/pagination)..
        * `POST /shared_recipes/{recipe_id}`: Share a recipe. (requires authentication, only creator).
        * `DELETE /shared_recipes/{recipe_id}`: unshare a recipe. (requires authentication, only creator).
    * **Tag API:**
        * `GET /tags`: Get all available tags.
    * **Favorite API (Optional):**
        * `GET /users/me/favorites`: Get the current user's favorite recipes.
        * `POST /users/me/favorites/{recipe_id}`: Add a recipe to favorites.
        * `DELETE /users/me/favorites/{recipe_id}`: Remove a recipe from favorites.
    * **Rating API (Optional):**
        * `POST /recipes/{recipe_id}/ratings`: Add or update a recipe rating.
        * `GET /recipes/{recipe_id}/ratings`: get recipe rating.
    * **Comment API (Optional):**
        * `GET /recipes/{recipe_id}/comments`: Get comments for a recipe.
        * `POST /recipes/{recipe_id}/comments`: Add a comment to a recipe.


5. Data Models (Pydantic)
* **User:**
    ```python
    from typing import Optional
    from sqlmodel import SQLModel, Field

    class User(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        email: str = Field(unique=True, index=True)
        password: str  # Store hashed passwords, not plain text!
        first_name: str
        last_name: str
    ```
* **Recipe:**
    ```python
    from typing import List, Optional
    from sqlmodel import SQLModel, Field, Relationship
    from datetime import datetime

    class Recipe(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        user_id: int = Field(foreign_key="user.id")
        title: str
        description: str
        ingredients: List[str]
        instructions: List[str]
        tags: List["Tag"] = Relationship(back_populates="recipes", link_model=RecipeTag)
        prep_time: int  # in minutes
        cook_time: int  # in minutes
        servings: int
        image_url: Optional[str]
        is_shared: bool = False
        created_at: datetime = Field(default_factory=datetime.utcnow)
        updated_at: datetime = Field(default_factory=datetime.utcnow)
        user: "User" = Relationship(back_populates="recipes")

class RecipeTag(SQLModel, table=True):
    recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    recipes: List["Recipe"] = Relationship(back_populates="tags", link_model=RecipeTag)

class SharedRecipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")

class Favorite(SQLModel, table=True): #optional
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id", primary_key=True)

class Rating(SQLModel, table=True): #optional
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id", primary_key=True)
    rating: int

class Comment(SQLModel, table=True): #optional
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    recipe_id: int = Field(foreign_key="recipe.id")
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

```

* **Pydantic models** will be created for request and response data, ensuring data validation at the API level.  These models will likely mirror the SQLModel models, but may have slight differences (e.g., omitting the `id` for create requests).


6. UI Design (shadcn/ui)
* **Style Guide:** Consistent use of Tailwind CSS and shadcn/ui components to create a clean and modern design.
* **Layout:**
    * Responsive layout that adapts to different screen sizes.
    * Clear separation of content areas.
    * Consistent navigation.
* **Key Pages:**
    * **Home Page:**
        * Welcome message.
        * Featured recipes (shared recipes).
        * Search bar.
        * Call to action (e.g., "Create your first recipe").
    * **Recipe List Page:**
        * Display of recipe cards (title, image, author, tags, rating).
        * Filters (by tag, search).
        * Pagination.
        * Sorting options (e.g., by title, date).
    * **Recipe Detail Page:**
        * Full recipe information (title, description, ingredients, instructions, image, author, prep/cook time, servings, source).
        * Option to share a recipe.
        * Comments section (if enabled).
        * Rating display (if enabled).
    * **User Profile Page:**
        * Display of user's recipes (private and shared).
        * User profile information.
        * Settings (ability to update profile).
    * **Create/Edit Recipe Page:**
        * Form for creating or editing recipes.
        * Input validation.
        * Image upload.
    * **Search Results Page:**
        * Display of recipes matching search criteria.
    * **Favorite Recipes Page**
         * Display of user's favorite recipes
* **Components:**
    * Recipe Card: Reusable component to display a summary of a recipe.
    * Search Bar: Component for searching recipes.
    * Tag Filter: Component for filtering recipes by tag.
    * Form Input: Reusable component for form fields.
    * Button: Reusable button component.
    * Navigation Bar: Component for site navigation.


7. Security
* **Authentication:**
    * Secure storage of user credentials (hashing passwords using bcrypt or similar).
    * JWT-based authentication for API requests.
    * Protection against brute-force attacks (rate limiting).
* **Authorization:**
    * Role-Based Access Control (RBAC) to restrict access to resources.
    * Only allow recipe creators to edit/delete their own recipes.
    * Properly authorize access to shared recipes.
* **Data Validation:**
    * Server-side validation of all input data using Pydantic to prevent injection attacks.
    * Client-side validation in React forms for a better user experience.
* ** protection of CSRF:**
    * Implement CSRF protection measures (e.g., using `CsrfViewMiddleware` in FastAPI, if a library supports it, or setting the appropriate headers).
* ** protection of XSS:**
    * Sanitize user-generated content on both the client and server sides to prevent XSS attacks.  React helps with this by default, but ensure you are using secure coding practices.
* ** protection of directories:**
    * Ensure that file uploads are handled securely to prevent directory traversal vulnerabilities.  Use Supabase Storage's features to help with this.


8. Internationalization
* **support for different languages on the UI level
* **support for different languages for the stored data
* **support for both LTR &	 RTL languages


9. Testing
* **Use relevant testing libraries according the tech stack
* **Unit tests for backend logic.
* **Integration tests for API endpoints.
* **UI tests for presentation logic
 
9. Future Enhancements
* Social features: Following users, activity feeds logins.
* Recipe import from URLs.
* Scaling the database.
* Meal planning features.
* Nutritional information for recipes.
* Support for different dietary restrictions.
* Food allergies support