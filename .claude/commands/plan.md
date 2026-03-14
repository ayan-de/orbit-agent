# Plan Command

Create implementation plan for features.

## Usage

```
/plan "Add user authentication"
/plan "Refactor agent graph for better error handling"
```

## Output

Creates a structured implementation plan:

```markdown
# Implementation Plan: Add User Authentication

## Overview
Add JWT-based authentication to the API endpoints.

## Files to Modify
- src/api/middleware/auth.py (new)
- src/api/router.py
- src/db/models.py
- src/db/repositories/user_repo.py (new)

## Implementation Steps

### Phase 1: Database Schema
1. Create User model with hashed passwords
2. Add migration for users table
3. Create UserRepository with CRUD operations

### Phase 2: Authentication Middleware
1. Implement JWT token generation
2. Create authentication middleware
3. Add rate limiting for login endpoint

### Phase 3: API Endpoints
1. POST /auth/register - Create new user
2. POST /auth/login - Authenticate and return token
3. GET /auth/me - Get current user

### Phase 4: Testing
1. Unit tests for UserRepository
2. Integration tests for auth endpoints
3. E2E test for full auth flow

## Dependencies
- python-jose[cryptography] for JWT
- passlib[bcrypt] for password hashing

## Risks
- Token refresh strategy needed
- Rate limiting critical for security

## Estimated Effort
- Phase 1: 2 hours
- Phase 2: 3 hours
- Phase 3: 2 hours
- Phase 4: 2 hours
- Total: ~9 hours
```
