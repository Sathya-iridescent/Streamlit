# Application Structure

## Modular Architecture

The application has been refactored into a clean, modular structure:

```
POExtract/
├── app.py                 # Main Flask application entry point
├── config.py              # Application constants (FACTORIES, BUYERS, etc.)
├── database.py            # Database connection and session management
├── extractor.py           # PDF extraction logic
│
├── models/                # Database models
│   ├── __init__.py
│   ├── user.py           # User model (authentication)
│   ├── po_item.py        # PO Item model
│   └── style_master.py   # Style Master model
│
├── routes/                # Route handlers (Blueprints)
│   ├── __init__.py
│   ├── auth_routes.py    # Login, logout, signup, profile
│   ├── po_routes.py      # Upload, download, update PO items
│   ├── dashboard_routes.py  # Dashboard view
│   └── style_master_routes.py  # Style master management
│
├── auth/                  # Authentication utilities
│   ├── __init__.py
│   ├── decorators.py     # @login_required, @admin_required
│   └── helpers.py        # login_user(), logout_user(), get_current_user()
│
├── utils/                 # Helper functions
│   ├── __init__.py
│   └── helpers.py        # Date calculations, formatting utilities
│
└── templates/             # HTML templates
    ├── auth/             # Authentication templates
    │   ├── login.html
    │   ├── signup.html
    │   └── profile.html
    ├── dashboard.html
    ├── upload.html
    ├── style_master.html
    └── results.html
```

## Authentication System

### Features
- **User Registration**: Sign up with username, email, password
- **User Login**: Secure password authentication
- **Session Management**: Persistent sessions with secure cookies
- **Route Protection**: `@login_required` decorator protects routes
- **User Profile**: View and update user information

### User Model
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password (using werkzeug)
- `full_name`, `phone`, `company`: Profile information
- `role`: User role (user, admin)
- `is_active`, `is_verified`: Account status
- `created_at`, `last_login`, `updated_at`: Timestamps

### Protected Routes
All routes except login/signup require authentication:
- `/dashboard` - Requires login
- `/upload` - Requires login
- `/style-master` - Requires login
- `/profile` - Requires login

### Public Routes
- `/` - Redirects to login or dashboard
- `/auth/login` - Login page
- `/auth/signup` - Registration page
- `/health` - Health check (no auth required)

## Database Models

### User Model (`models/user.py`)
- Authentication and user profile
- Password hashing with werkzeug
- Session management support

### POItem Model (`models/po_item.py`)
- Purchase Order items
- Foreign key to StyleMaster via EAN
- All PO-related fields

### StyleMaster Model (`models/style_master.py`)
- EAN to Style/Buyer mappings
- Unique EAN constraint
- Relationship to POItem

## Route Organization

### Authentication Routes (`routes/auth_routes.py`)
- `GET/POST /auth/login` - User login
- `GET/POST /auth/signup` - User registration
- `GET /auth/logout` - User logout
- `GET /auth/profile` - User profile page
- `POST /auth/profile/update` - Update profile

### PO Routes (`routes/po_routes.py`)
- `GET /` - Home (redirects to upload)
- `GET/POST /upload` - Upload PDF files
- `GET /download_excel` - Download dashboard as Excel
- `POST /update_field` - Update PO item field

### Dashboard Routes (`routes/dashboard_routes.py`)
- `GET /dashboard` - Main dashboard view

### Style Master Routes (`routes/style_master_routes.py`)
- `GET /style-master` - Style master management
- `POST /save_style` - Save/update style entry
- `GET /delete_style/<id>` - Delete style entry
- `GET /refresh_styles` - Refresh PO items from style master

## Usage

### First Time Setup

1. **Set SECRET_KEY in .env:**
   ```bash
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
   ```
   Add the output to your `.env` file.

2. **Run the application:**
   ```bash
   FLASK_ENV=development python app.py
   ```

3. **Create your first user:**
   - Visit `/auth/signup`
   - Register with username, email, password
   - Login at `/auth/login`

### Development

- All routes are protected by default (except auth routes)
- Use `@login_required` decorator to protect new routes
- User session persists across browser restarts
- Profile information can be updated via `/auth/profile`

### Production

- Set `FLASK_ENV=production` in environment
- Set strong `SECRET_KEY` in environment variables
- Sessions use secure cookies in production
- All routes require authentication

## Migration Notes

The old monolithic `app.py` has been split into:
- **Models**: Separated into `models/` directory
- **Routes**: Organized into blueprints in `routes/`
- **Auth**: Authentication logic in `auth/`
- **Utils**: Helper functions in `utils/`
- **Config**: Constants in `config.py`

All existing functionality is preserved, now with authentication and better organization.


