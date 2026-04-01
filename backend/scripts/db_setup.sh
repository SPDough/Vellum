#!/bin/bash

# Database setup script for Otomeshon Banking Platform
# This script sets up the database, runs migrations, and seeds initial data

set -e  # Exit on any error

echo "🏦 Otomeshon Banking Platform - Database Setup"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PostgreSQL is running
check_postgres() {
    print_status "Checking PostgreSQL connection..."
    
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_success "PostgreSQL is running"
    else
        print_error "PostgreSQL is not running or not accessible"
        print_status "Please start PostgreSQL and ensure it's accessible on localhost:5432"
        exit 1
    fi
}

# Create database if it doesn't exist
create_database() {
    print_status "Creating database if it doesn't exist..."
    
    # Get database URL from environment or use default
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_USER=${DB_USER:-app}
    DB_PASSWORD=${DB_PASSWORD:-changeme}
    DB_NAME=${DB_NAME:-otomeshon}
    
    # Check if database exists
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        print_success "Database '$DB_NAME' already exists"
    else
        print_status "Creating database '$DB_NAME'..."
        createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
        print_success "Database '$DB_NAME' created"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements-core.txt" ]; then
        pip install -r requirements-core.txt
        print_success "Core dependencies installed"
    else
        print_warning "requirements-core.txt not found, skipping dependency installation"
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Initialize Alembic if not already done
    if [ ! -d "migrations/versions" ] || [ -z "$(ls -A migrations/versions)" ]; then
        print_status "Initializing database schema..."
        python scripts/migration_utils.py upgrade
    else
        print_status "Upgrading to latest schema..."
        python scripts/migration_utils.py upgrade
    fi
    
    print_success "Database migrations completed"
}

# Seed initial data
seed_database() {
    print_status "Seeding initial data..."
    
    python scripts/seed_database.py seed
    
    print_success "Database seeding completed"
}

# Validate setup
validate_setup() {
    print_status "Validating database setup..."
    
    python scripts/migration_utils.py validate
    
    print_success "Database setup validation completed"
}

# Main setup function
main() {
    echo
    print_status "Starting database setup process..."
    echo
    
    # Parse command line arguments
    SKIP_DEPS=false
    SKIP_SEED=false
    ENVIRONMENT=${ENVIRONMENT:-development}
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-seed)
                SKIP_SEED=true
                shift
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-deps     Skip Python dependency installation"
                echo "  --skip-seed     Skip database seeding"
                echo "  --environment   Set environment (development|testing|production)"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_status "Environment: $ENVIRONMENT"
    echo
    
    # Banking compliance warning for production
    if [ "$ENVIRONMENT" = "production" ]; then
        print_warning "PRODUCTION ENVIRONMENT DETECTED"
        print_warning "Ensure all changes comply with banking regulations"
        print_warning "Consider creating a backup before proceeding"
        echo
        read -p "Continue with production setup? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            print_status "Setup cancelled"
            exit 0
        fi
    fi
    
    # Step 1: Check PostgreSQL
    check_postgres
    echo
    
    # Step 2: Install dependencies
    if [ "$SKIP_DEPS" = false ]; then
        install_dependencies
        echo
    fi
    
    # Step 3: Create database
    create_database
    echo
    
    # Step 4: Run migrations
    run_migrations
    echo
    
    # Step 5: Seed data (skip in production)
    if [ "$SKIP_SEED" = false ] && [ "$ENVIRONMENT" != "production" ]; then
        seed_database
        echo
    elif [ "$ENVIRONMENT" = "production" ]; then
        print_warning "Skipping database seeding in production environment"
        echo
    fi
    
    # Step 6: Validate
    validate_setup
    echo
    
    print_success "Database setup completed successfully!"
    echo
    print_status "Next steps:"
    echo "  1. Start the application: uvicorn app.main:app --reload"
    echo "  2. Access API docs: http://localhost:8000/docs"
    echo "  3. Check monitoring: http://localhost:8000/monitoring/health"
    echo
    
    if [ "$ENVIRONMENT" = "development" ]; then
        print_status "Development credentials:"
        echo "  Admin: admin@otomeshon.com / SecureAdmin123!"
        echo "  Trader: trader1@otomeshon.com / TraderPass123!"
        echo "  Compliance: compliance@otomeshon.com / CompliancePass123!"
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi