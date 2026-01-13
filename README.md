# PO Extract Applications

A Flask web application for extracting and managing Purchase Order (PO) data from PDF files with user authentication and role-based access control.

## Features

- **User Authentication**: Secure login, signup, and session management
- **Role-Based Access**: User and admin roles with different privileges
- **Upload PDFs**: Upload multiple PO PDF files for processing
- **Extract Data**: Automatically extracts PO information from PDFs
- **Dashboard**: View and manage all PO items with inline editing
- **Style Master**: Manage EAN to Style Number and Buyer mappings
- **Excel Export**: Download dashboard data as Excel file
- **User Profile**: View and update user information
- **PostgreSQL Database**: Production-grade database with foreign key relationships
- **Modular Architecture**: Clean separation of routes, models, and utilities

## Prerequisites

- Python 3.8 or higher
- PostgreSQL (for production) or SQLite (for development)
- Virtual environment (recommended)

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd POExtract
```

### 2. Create and activate virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update with your database credentials:

```bash
cp .env.example .env
```

Generate a secure secret key for sessions:
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Edit `.env` file:

```env
# Security (REQUIRED)
SECRET_KEY=your-generated-secret-key-here

# Database Configuration
DB_TYPE=postgresql         
DB_HOST=localhost
DB_PORT=5432
DB_NAME=poextract_db
DB_USER=postgres
DB_PASSWORD=your_password

# Flask Configuration
FLASK_ENV=development        # 'development' or 'production'
FLASK_DEBUG=True             # True for dev, False for production
PORT=5001                    # Port for development server
SESSION_TIMEOUT=3600         # Session timeout in seconds (default: 1 hour)
```

**Important**: The `SECRET_KEY` is required for authentication and session management. Never commit it to version control.

## Running the Application

### Development Mode (Recommended for Local Development)

Development mode uses Flask's built-in development server with auto-reload and debug features:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Set development environment
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run the application
python app.py
```

Or use the shorthand:
```bash
FLASK_ENV=development FLASK_DEBUG=True python app.py
```

The application will start on **http://127.0.0.1:5001** (or the port specified in `.env`).

**Development Mode Features:**
- ✅ Auto-reload on code changes
- ✅ Debug mode enabled (detailed error pages)
- ✅ Flask development server
- ✅ Runs on port 5001 (configurable via PORT env var)

### Production Mode (For Render.com Deployment)

Production mode uses Waitress server (configured for Render.com):

```bash
# Set production environment
export FLASK_ENV=production

# Run the application
python app.py
```

**Production Mode Features:**
- ✅ Waitress WSGI server (production-ready)
- ✅ Runs on port 10000 (or PORT env var)
- ✅ No debug mode
- ✅ Optimized for production

### Quick Start (Development)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run in development mode
FLASK_ENV=development python app.py

# 3. Open browser
# http://localhost:5001
```

## Database Setup

### PostgreSQL (Production)

1. Create a PostgreSQL database:
   ```bash
   createdb poextract_db
   ```

2. Update `.env` with your PostgreSQL credentials

3. Tables are automatically created on first run via `initialize_db()`

### SQLite (Development)

1. Set `DB_TYPE=sqlite` in `.env`

2. Database file `poextract.db` will be created automatically

3. Tables are automatically created on first run

### Migrating from SQLite to PostgreSQL

If you have existing SQLite data to migrate:

```bash
# 1. Ensure PostgreSQL is running and .env is configured
# 2. Run migration script
python migrate_to_postgresql.py
```

## User Management

### Creating Your First User

After starting the application, you can create a user account:

1. Visit `http://localhost:5001/auth/signup`
2. Fill in username, email, and password
3. Login at `http://localhost:5001/auth/login`

### Creating an Admin User

To create an admin account with full privileges:

```bash
python create_admin.py
```

Or with specific credentials:
```bash
python create_admin.py --username admin --email admin@example.com --password secure_password
```

The script will prompt for missing information interactively.

### Changing User Roles

To change a user's role (e.g., promote to admin):

```bash
python change_user_role.py --username username --role admin
```

Available roles: `user`, `admin`

### Resetting Admin Password

If you need to reset an admin password:

```bash
python reset_admin_password.py --username admin
```

## Project Structure

```
POExtract/
├── app.py                      # Main Flask application entry point
├── config.py                   # Application constants (FACTORIES, BUYERS, etc.)
├── database.py                 # Database connection and session management
├── extractor.py                # PDF text extraction and parsing logic
│
├── models/                     # Database models
│   ├── __init__.py
│   ├── user.py                # User model (authentication)
│   ├── po_item.py             # PO Item model
│   └── style_master.py        # Style Master model
│
├── routes/                     # Route handlers (Blueprints)
│   ├── __init__.py
│   ├── auth_routes.py         # Login, logout, signup, profile
│   ├── po_routes.py           # Upload, download, update PO items
│   ├── dashboard_routes.py    # Dashboard view
│   └── style_master_routes.py # Style master management
│
├── auth/                       # Authentication utilities
│   ├── __init__.py
│   ├── decorators.py          # @login_required, @admin_required
│   └── helpers.py             # login_user(), logout_user(), get_current_user()
│
├── utils/                      # Helper functions
│   ├── __init__.py
│   └── helpers.py             # Date calculations, formatting utilities
│
├── templates/                  # HTML templates
│   ├── auth/                  # Authentication templates
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── profile.html
│   │   └── admin_users.html
│   ├── dashboard.html
│   ├── style_master.html
│   ├── upload.html
│   └── results.html
│
├── uploads/                    # Directory for uploaded PDF files
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment variables template
├── render.yaml                 # Render.com deployment configuration
├── Procfile                    # Process file for deployment
├── runtime.txt                 # Python version specification
│
├── create_admin.py             # Script to create admin users
├── change_user_role.py         # Script to change user roles
├── reset_admin_password.py     # Script to reset admin passwords
└── migrate_to_postgresql.py    # Migration script for SQLite to PostgreSQL
```

## Database Schema

### `users` Table
- `id` (PRIMARY KEY, auto-increment)
- `username` (UNIQUE) - Username for login
- `email` (UNIQUE) - Email address
- `password_hash` - Hashed password (using werkzeug)
- `full_name` - Full name
- `phone` - Phone number
- `company` - Company name
- `role` - User role (`user` or `admin`)
- `is_active` - Account active status
- `is_verified` - Email verification status
- `created_at` - Account creation timestamp
- `last_login` - Last login timestamp
- `updated_at` - Last update timestamp

### `style_master` Table
- `id` (PRIMARY KEY, auto-increment)
- `ean` (UNIQUE, indexed) - European Article Number
- `style_no` - Style number
- `buyer` - Buyer name

### `po_items` Table
- `id` (PRIMARY KEY, auto-increment)
- `ean` (FOREIGN KEY → `style_master.ean`)
- `po_number` - Purchase Order number
- `style` - Style (populated from style_master)
- `buyer` - Buyer (populated from style_master)
- `factory` - Factory name
- `transporter` - Transporter name
- `delivery_date` - Delivery date
- `quantity` - Quantity
- `factory_remarks` - Factory remarks
- `created_at` - Timestamp

## Deployment

### Render.com

1. Push your code to GitHub

2. In Render Dashboard:
   - Create PostgreSQL database
   - Create Web Service
   - Connect GitHub repository
   - Render will use `render.yaml` for configuration

3. The app will automatically:
   - Install dependencies
   - Connect to PostgreSQL
   - Start with Waitress on port 10000

See `render.yaml` for deployment configuration.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Secret key for sessions and authentication | - | **Yes** |
| `DB_TYPE` | Database type (`postgresql` or `sqlite`) | `sqlite` | No |
| `DB_HOST` | PostgreSQL host | `localhost` | Yes (if PostgreSQL) |
| `DB_PORT` | PostgreSQL port | `5432` | Yes (if PostgreSQL) |
| `DB_NAME` | Database name | `poextract_db` | Yes (if PostgreSQL) |
| `DB_USER` | Database user | `postgres` | Yes (if PostgreSQL) |
| `DB_PASSWORD` | Database password | - | Yes (if PostgreSQL) |
| `DATABASE_URL` | Full database URL (Render/Heroku style) | - | No (alternative to above) |
| `FLASK_ENV` | Flask environment (`development` or `production`) | `development` | No |
| `FLASK_DEBUG` | Enable debug mode | `True` | No |
| `PORT` | Server port | `5001` (dev) / `10000` (prod) | No |
| `SESSION_TIMEOUT` | Session timeout in seconds | `3600` (1 hour) | No |

## Authentication & Security

### Protected Routes

All routes except authentication endpoints require login:
- `/dashboard` - Requires login
- `/upload` - Requires login
- `/style-master` - Requires login
- `/profile` - Requires login

### Public Routes

- `/` - Redirects to login or dashboard (based on auth status)
- `/auth/login` - Login page
- `/auth/signup` - Registration page
- `/health` - Health check (no auth required)

### Session Management

- Sessions use secure cookies in production
- Default session timeout: 1 hour (configurable via `SESSION_TIMEOUT`)
- Sessions persist across browser restarts
- Secure cookie settings enabled in production mode

## Development Tips

### Running Tests

```bash
# Test database connection
python test_psql_connection.py

# Test app connection
python test_app_connection.py

# Test functionality
python test_functionality.py
```

### Resetting Database

```bash
# Reset PostgreSQL database (drops and recreates tables)
python reset_database.py

# Complete database drop (PostgreSQL only)
python drop_database_complete.py
```

### Viewing Logs

Development mode shows detailed logs in the terminal. For production on Render, check the Render dashboard logs.

## Troubleshooting

### Port Already in Use

If port 5001 is in use, change it in `.env`:
```env
PORT=5002
```

### Database Connection Errors

1. Verify PostgreSQL is running:
   ```bash
   psql -U postgres -l
   ```

2. Check `.env` file has correct credentials

3. Test connection:
   ```bash
   python test_psql_connection.py
   ```

### Import Errors

Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Authentication Issues

1. **"Secret key not set" error:**
   - Ensure `SECRET_KEY` is set in `.env` file
   - Generate a new key: `python3 -c "import secrets; print(secrets.token_hex(32))"`

2. **Session not persisting:**
   - Check `SECRET_KEY` is set correctly
   - Verify `SESSION_TIMEOUT` is not too short
   - Clear browser cookies and try again

3. **Cannot login:**
   - Verify user exists: Check database or create new user via signup
   - Reset password: Use `reset_admin_password.py` for admin accounts
   - Check database connection is working

## API Endpoints

### Authentication
- `GET/POST /auth/login` - User login
- `GET/POST /auth/signup` - User registration
- `GET /auth/logout` - User logout
- `GET /auth/profile` - User profile page
- `POST /auth/profile/update` - Update profile

### PO Management
- `GET /` - Home (redirects to upload)
- `GET/POST /upload` - Upload PDF files
- `GET /download_excel` - Download dashboard as Excel
- `POST /update_field` - Update PO item field

### Dashboard
- `GET /dashboard` - Main dashboard view

### Style Master
- `GET /style-master` - Style master management
- `POST /save_style` - Save/update style entry
- `GET /delete_style/<id>` - Delete style entry
- `GET /refresh_styles` - Refresh PO items from style master

## License

[Your License Here]

## Support

[tushar - tusharrravindran@gmail.com]
