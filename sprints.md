# Sprint Planning

- P0: Critical path/blocking
- P1: High priority
- P2: Medium priority
- P3: Nice to have

choosing the model for Cursor IDE - https://docs.cursor.com/guides/selecting-models

## Sprint 1 - Foundation (Weeks 1-2)
Focus: Basic infrastructure and core backend setup

### Backend (P0)
- #1 Set up FastAPI project structure and basic configuration - DONE
- #2 Configure Supabase connection and environment variables - DONE
- #3 Implement database migrations using Alembic - DONE
- #4 Set up CORS middleware and applicative error handling - DONE
- #7 Create initial database migration for User model - DONE
- #14 Implement user registration endpoint - DONE
- #15 Implement user login endpoint with JWT - DONE

### Frontend (P0)
- #46 Set up React project with TypeScript - DONE
- #47 Configure Tailwind CSS and shadcn/ui - DONE
- #48 Set up React Router configuration - DONE
- #50 Set up authentication context/state management - DONE
- #49 Implement basic layout components - PARTIALLY DONE
- #51 Configure API client with authentication - PARTIALLY DONE
- #52 Create login page component - DONE
- #53 Create registration page component
- #54 Implement registration form with validation - DONE
- #57 Create recipe list page component
- #103 Create my recipes page component

### Documentation (P1)
- #98 Write deployment documentation

## Sprint 2 - Core Recipe Features (Weeks 3-4)
Focus: Basic recipe management functionality

### Backend (P0)
- #8 Create database migration for Recipe model - DONE
- #9 Create database migration for Tag and RecipeTag models
- #21 Implement create recipe endpoint
- #22 Implement get single recipe endpoint
- #23 Implement update recipe endpoint
- #24 Implement delete recipe endpoint

### Frontend (P0)
- #49 Implement basic layout components
- #51 Configure API client with authentication
- #52 Create login page component - DONE
- #53 Create registration page component
- #54 Implement registration form with validation - DONE
- #57 Create recipe list page component
- #58 Create recipe card component
- #103 Create my recipes page component

### Testing (P1)
- #83 Write unit tests for backend models - PARTIALLY DONE
- #84 Create API endpoint integration tests
- #102 Write tests for user registration endpoint - DONE

## Sprint 3 - Recipe Enhancement (Weeks 5-6)
Focus: Recipe sharing and tags

### Backend (P0)
- #30 Implement share recipe endpoint
- #31 Implement unshare recipe endpoint
- #32 Create shared recipes listing endpoint
- #35 Implement create tag endpoint
- #36 Implement get all tags endpoint
- #37 Implement add tags to recipe endpoint

### Frontend (P0)
- #59 Create recipe detail page component
- #60 Implement recipe creation form
- #61 Create recipe edit form component
- #63 Create tag selection component
- #65 Create shared recipes view

### Security (P1)
- #89 Add CSRF protection
- #90 Configure secure headers
- #91 Implement input sanitization

## Sprint 4 - User Experience (Weeks 7-8)
Focus: Search, filters, and user profile

### Backend (P1)
- #25 Implement list recipes endpoint with pagination
- #26 Add recipe search functionality by title
- #27 Add recipe filtering by tags
- #17 Implement user profile retrieval endpoint
- #18 Implement user profile update endpoint

### Frontend (P1)
- #69 Create search bar component
- #70 Implement tag filter component
- #71 Create search results page
- #73 Add pagination controls
- #55 Create user profile page component
- #56 Implement profile editing functionality

### Testing (P1)
- #85 Write frontend component unit tests
- #86 Create end-to-end testing suite

## Sprint 5 - Optional Features (Weeks 9-10)
Focus: Ratings, comments, and favorites

### Backend (P2)
- #39 Implement favorite recipe functionality
- #40 Implement unfavorite recipe functionality
- #42 Implement recipe rating system
- #44 Create comment system endpoints

### Frontend (P2)
- #74 Create favorites management UI
- #75 Implement recipe rating component
- #76 Create comments section component

### Performance (P1)
- #92 Add API request caching
- #93 Optimize database queries
- #94 Implement error logging system

## Sprint 6 - Internationalization & Polish (Weeks 11-12)
Focus: i18n support and documentation

### Internationalization (P2)
- #78 Set up i18n infrastructure
- #79 Create English language pack
- #80 Create Hebrew language pack (RTL support)
- #81 Implement language switcher component
- #82 Add RTL layout support

### Documentation (P1)
- #95 Create API documentation
- #96 Write frontend component documentation
- #97 Create database schema documentation
- #99 Create user guide
- #100 Write developer onboarding guide

## Backlog (P3)
Nice to have features that can be implemented as needed:
- #16 Implement password reset functionality and password update functionality and exclude password from user_update endpoint 
- #19 Add email verification system
- #28 Implement ingredient search functionality
- #29 Add recipe image upload to Supabase Storage
- #72 Implement advanced search filters
- #77 Implement shopping list feature UI
- #88 Implement rate limiting
- #101 Add more comprehensive tests (unit, integration, e2e)
- #104 add monitoring support including app health and performance
- #105 add password invalidation after n days?
- #106 allow 

## Tests Backlog (P3)
More test that can be implemented:
### Integration tests
- email uniqness on user creation and user update
### Unit ttests
- recipes unit tests

## Dependencies
- Frontend authentication views depend on backend authentication endpoints
- Recipe management UI depends on recipe core functionality endpoints
- Search and filter UI depends on corresponding backend endpoints
- Optional features frontend depends on optional features backend
- Testing should be implemented alongside feature development
- Security measures should be implemented before deployment