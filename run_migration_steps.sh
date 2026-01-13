#!/bin/bash
# Step-by-Step Migration Script
# Run this script to execute migration in the correct order

echo "============================================================"
echo "PostgreSQL Migration - Step by Step"
echo "============================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env file template..."
    cat > .env << EOF
# Database Configuration
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=poextract_db
DB_USER=$(whoami)
DB_PASSWORD=

# Flask Configuration
SECRET_KEY=dev-secret-key-change-in-production
FLASK_DEBUG=False
EOF
    echo "✓ Created .env file template"
    echo ""
    echo "⚠️  Please edit .env and set DB_PASSWORD before continuing"
    echo "   Press Enter when ready, or Ctrl+C to exit and edit .env manually"
    read
fi

echo "Step 1: Testing PostgreSQL Connectivity..."
python test_psql_connection.py
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Step 1 FAILED - Fix PostgreSQL connection issues first"
    exit 1
fi

echo ""
echo "Step 2: Testing App Connection to PostgreSQL..."
python test_app_connection.py
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Step 2 FAILED - Fix app connection issues first"
    exit 1
fi

echo ""
echo "Step 3: Migrating SQLite → PostgreSQL..."
python migrate_to_postgresql.py
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Step 3 FAILED - Migration failed"
    exit 1
fi

echo ""
echo "Step 4: Testing Migration (Comparing SQLite vs PostgreSQL)..."
python test_migration.py
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Step 4 had issues - Review the output above"
    echo "   Migration may have succeeded but data comparison found differences"
fi

echo ""
echo "Step 5: Testing Functionality..."
python test_functionality.py
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Step 5 had issues - Review the output above"
fi

echo ""
echo "============================================================"
echo "Migration Process Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Review test results above"
echo "  2. Start the app: python app.py"
echo "  3. Test the application manually in browser"
echo ""




