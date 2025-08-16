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
- #49 Implement basic layout components - DONE
- #51 Configure API client with authentication - PARTIALLY DONE
- #52 Create login page component - DONE
- #53 Create registration page component - DONE
- #54 Implement registration form with validation - DONE
- #57 Create recipe list page component - DONE
- #103 Create my recipes page component - DONE

### Documentation (P1)
- #98 Write deployment documentation - TBD

## Sprint 2 - Core Recipe Features (Weeks 3-4)
Focus: Basic recipe management functionality

### Backend (P0)
- #8 Create database migration for Recipe model - PARTIALLY DONE
- #21 Implement create recipe endpoint - DONE
- #22 Implement get single recipe endpoint - DONE
- #23 Implement update recipe endpoint - DONE
- #24 Implement delete recipe endpoint - DONE

### Frontend (P0)
- #49 Implement basic layout components - DONE
- #109 Implement Tag service - DONE
- #110 Add the Tag endpoints (with sparation to recipe endpoint and admin endpoint)
- #51 Configure API client with authentication - DONE
- #52 Create login page component - DONE
- #53 Create registration page component - DONE
- #54 Implement registration form with validation - DONE
- #57 Create recipe list page component - DONE
- #58 Create recipe card component - DONE 
- #103 Create my recipes page component - DONE

### Testing (P1)
- #83 Write unit tests for backend models - PARTIALLY DONE
- #84 Create API endpoint integration tests PARTIALLY DONE
- #102 Write tests for user registration endpoint - DONE

## Sprint 3 - Recipe Enhancement (Weeks 5-6)
Focus: Recipe sharing and tags

### Backend (P0)
- #9 Create database migration for Tag and RecipeTag models - DONE
- #30 Implement share recipe endpoint - 
- #31 Implement unshare recipe endpoint - 
- #32 Create shared recipes listing endpoint - 
- #35 Implement create tag endpoint - 
- #36 Implement get all tags endpoint -
- #37 Implement add tags to recipe endpoint -

### Frontend (P0)
- #59 Create recipe detail page component - DONE
- #60 Implement recipe creation form - DONE
- #61 Create recipe edit form component - DONE
- #63 Create tag selection component -
- #65 Create shared recipes view - 

### Security (P1)
- #89 Add CSRF protection
- #90 Configure secure headers - DONE
- #91 Implement input sanitization

## Sprint 4 - User Experience (Weeks 7-8)
Focus: Search, filters, and user profile

### Backend (P1)
- #25 Implement list recipes endpoint with pagination - DONE
- #26 Add recipe search functionality by title - DONE
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
- #16 enhance login handling: password reset, password invalidation after n days, token expiration, redirect to login on error after timeout 
- #19 Add email verification system - send email and wait for confirmation
- #28 Implement ingredient search functionality - DONE
- #29 Add recipe image upload to Supabase Storage 
- #72 Implement advanced search filters
- #77 Implement shopping list feature
- #88 Implement rating system for recipes
- #101 Add more comprehensive tests (unit, integration, e2e)
- #104 add monitoring support including app health and performance
- #105 add secure token storage (now could only use httpOnly cookies)
- #106 add admin endpoint - DONE
- #107 add multiplicity to image uploads
- #108 add AI support for creating a recipe by understanding its text using OCR (using translation or not?) based on an uploaded image

## Tests Backlog (P3)
### Gaps Identified in the fronend code base (14.8.2025):
- ❌ Missing tests for HomePage and AboutPage (defined inline in main.tsx)
- ❌ Missing tests for AuthProvider component
- ❌ Missing tests for utility functions
- ❌ No integration tests for complete user flows
- ❌ Limited accessibility testing
- ❌ No performance or visual regression tests
- CRITICAL (Must have for production readiness)
    1. Missing Page Component Tests
        - HomePage.test.tsx - The main landing page component (defined in main.tsx)
        - AboutPage.test.tsx - The about page component (defined in main.tsx)
        - App.test.tsx - The main App component (currently shows Vite default content)
    2. Missing Context Provider Tests
        - AuthProvider.test.tsx - The AuthProvider component that wraps the entire app
        - AuthContext.test.tsx - Already exists but may need enhancement for provider testing
    3. Missing Utility Function Tests
        - utils.test.ts - Test the cn() utility function for class name merging
        - config.test.ts - Test configuration constants
    4. Integration Tests
        - App Integration Tests - Test the complete app routing and component integration
        - Authentication Flow Tests - End-to-end tests for login → protected routes → logout flow
        - Recipe CRUD Flow Tests - Complete workflow tests for creating, reading, updating, deleting recipes

- IMPORTANT (Should have for good test coverage)
    1. Missing Component Tests
        - Error Boundary Tests - Test error handling and fallback UI
        - Loading State Tests - Comprehensive loading state testing across components
        - Accessibility Tests - Test ARIA labels, keyboard navigation, screen reader compatibility
    2. Enhanced Existing Tests
        - RecipeCard.test.tsx - Add tests for different variants (public vs private, with/without images)
        - MainLayout.test.tsx - Add tests for navigation state changes, responsive behavior
        - PageContainer.test.tsx - Add tests for different title/description combinations
    3. API Integration Tests
        - Enhanced api-client.test.ts - Add more edge cases, error scenarios, retry logic
        - Mock Service Worker Tests - Test API mocking and error simulation
    4. Form Validation Tests
        - Cross-field Validation Tests - Test validation that depends on multiple fields
        - Real-time Validation Tests - Test validation as user types
        - Form State Persistence Tests - Test form data persistence across navigation

- NICE-TO-HAVE (Quality of life improvements)
    1. Performance Tests
        - Component Render Performance Tests - Test rendering performance for large lists
        - Memory Leak Tests - Test for memory leaks in long-running components
        - Bundle Size Tests - Test that bundle size stays within acceptable limits
    2. Visual Regression Tests
        - Component Screenshot Tests - Test that UI components render correctly
        - Responsive Design Tests - Test components at different screen sizes
        - Theme/Dark Mode Tests - Test components in both light and dark themes
    3. User Interaction Tests
        - Keyboard Navigation Tests - Test tab order, keyboard shortcuts
        - Touch/Mobile Tests - Test touch interactions and mobile-specific behavior
        - Drag and Drop Tests - If any drag/drop functionality exists
    4. Edge Case Tests
        - Network Error Tests - Test behavior when network is slow/unavailable
        - Browser Compatibility Tests - Test in different browsers (if needed)
        - Localization Tests - If internationalization is planned      
    5. Test Infrastructure Improvements
        - Custom Test Utilities - Enhanced test helpers for common patterns
        - Test Data Factories - Better mock data generation
        - Test Coverage Thresholds - Enforce minimum coverage requirements


## Gaps Identified in the backend code base (14.8.2025):
- Immediate (Critical):
    - test_admin.py - Admin endpoints are exposed and need security testing
    - test_security.py - Security functions are critical for authentication
    - test_config.py - Configuration is fundamental to application startup
    - test_main.py - Main application logic needs testing
- Short-term (Important):
    - test_recipes_public.py - Public API endpoints need testing
    - test_dependencies.py - Dependency injection is used throughout
    - test_database_session.py - Database connections are critical
    - Integration tests - Complete user workflows
- Long-term (Nice-to-have):
    - Performance testing
    - Security penetration testing
    - Load testing
    - Monitoring and observability testing

## Dependencies
- Frontend authentication views depend on backend authentication endpoints
- Recipe management UI depends on recipe core functionality endpoints
- Search and filter UI depends on corresponding backend endpoints
- Optional features frontend depends on optional features backend
- Testing should be implemented alongside feature development
- Security measures should be implemented before deployment