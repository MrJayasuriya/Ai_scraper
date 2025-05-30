# Authentication System

## Overview

The AI Contact Scraper Pro now includes a complete user authentication system with signup, login, and session management. Each user has their own isolated data space.

## Features

### User Management
- **Sign Up**: Create new accounts with username, email, and password
- **Login**: Authenticate with username/email and password
- **Session Management**: Secure 30-day sessions with automatic cleanup
- **Data Isolation**: Each user only sees their own search results and scraped data

### Security Features
- **Password Hashing**: SHA-256 with salt for secure password storage
- **Session Tokens**: Cryptographically secure session tokens
- **Input Validation**: Username, email, and password validation
- **Account Management**: Deactivate accounts if needed

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

### Username Requirements
- 3-30 characters
- Letters, numbers, and underscores only

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Modified Tables
- `search_results` table now includes `user_id` foreign key
- All data operations are filtered by user context

## User Interface

### Authentication Page
- Clean, modern login/signup interface
- Integrated with the existing premium styling
- Real-time validation feedback
- Auto-login after successful signup

### User Dashboard
- User info displayed in sidebar
- Secure logout functionality
- User-specific statistics and data

## Data Isolation

### Search Results
- Each user only sees their own search results
- Database queries include user_id filtering
- Backward compatibility maintained for existing data

### Analytics
- Statistics calculated per user
- Charts and metrics show user-specific data
- Data export includes only user's data

### Data Management
- "Clear My Data" only affects current user's data
- Complete isolation between users

## Session Management

### Session Creation
- Generated on successful login/signup
- 30-day expiration by default
- Stored securely with user mapping

### Session Validation
- Automatic validation on each request
- Expired sessions are cleaned up
- Invalid sessions trigger re-authentication

### Logout
- Deactivates current session
- Clears all session state
- Redirects to login page

## Implementation Details

### File Structure
```
Ai_scraper/
├── src/
│   └── utils/
│       ├── database.py      # Extended with auth tables and methods
│       └── auth.py          # New authentication manager
└── streamlit_app.py         # Updated with auth integration
```

### Key Classes

#### `DatabaseManager` (Extended)
- User creation and authentication
- Session management
- User-specific data queries
- Password hashing and validation

#### `AuthManager` (New)
- Streamlit authentication forms
- Session state management
- Input validation
- User interface components

## Usage

### For Users
1. Access the application
2. Choose "Sign Up" to create an account or "Login" if you have one
3. Use the application normally - all data is automatically user-specific
4. Logout when finished

### For Developers
1. All existing functionality works unchanged
2. Database queries automatically include user context when authenticated
3. Use `auth_manager.get_current_user_id()` to get current user ID
4. Pass `user_id` parameter to database methods for user-specific operations

## Backward Compatibility

The system maintains full backward compatibility:
- Existing data remains accessible (user_id = NULL)
- Database migrations handle existing tables
- All existing functionality works without modification

## Security Considerations

1. **Password Storage**: Never stored in plain text, always hashed with salt
2. **Session Security**: Cryptographically secure tokens with expiration
3. **SQL Injection**: Parameterized queries protect against injection
4. **Input Validation**: All user inputs are validated before processing
5. **Session Cleanup**: Expired sessions are automatically cleaned up

## Future Enhancements

Possible future additions:
- Password reset functionality
- Email verification
- Role-based access control
- Account settings page
- Password change functionality
- Two-factor authentication 