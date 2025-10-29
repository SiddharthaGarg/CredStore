#!/bin/bash

# Product Reviews API - Easy Setup Script
# This script sets up Docker container, runs migrations, and inserts sample users

set -e  # Exit on any error

echo "🚀 Product Reviews API - Easy Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_info "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running or accessible. Please start Docker and try again."
        print_info "If you get permission errors, run this script with sudo: sudo ./setup.sh"
        exit 1
    fi
    print_status "Docker is running"
}

check_uv() {
    print_info "Checking uv..."
    if ! uv --version > /dev/null 2>&1; then
        print_error "uv is not installed. Please install uv and try again."
        exit 1
    fi
    print_status "uv is installed"
}

# Check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Neither 'docker-compose' nor 'docker compose' is available."
        exit 1
    fi
    print_status "Docker Compose is available: $DOCKER_COMPOSE_CMD"
}

# Clean up existing containers (keeps volumes to preserve data)
cleanup() {
    print_info "Stopping existing containers (data will be preserved)..."
    $DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    print_status "Containers stopped"
}

# Start PostgreSQL container
start_database() {
    print_info "Starting PostgreSQL container..."
    $DOCKER_COMPOSE_CMD up -d postgres
    
    print_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U postgres -d product_reviews > /dev/null 2>&1; then
            print_status "PostgreSQL is ready"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    print_error "PostgreSQL failed to start within 60 seconds"
    exit 1
}

# Run Liquibase migrations
run_migrations() {
    print_info "Running Liquibase migrations..."
    
    # Run Liquibase container to execute migrations
    $DOCKER_COMPOSE_CMD run --rm liquibase
    
    if [ $? -eq 0 ]; then
        print_status "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Set up Python environment with uv
setup_python_env() {
    print_info "Setting up Python environment with uv sync..."
    
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    # Use uv sync to create venv and install all dependencies
    print_info "Running uv sync (creates venv + installs dependencies)..."
    uv sync
    
    if [ $? -eq 0 ]; then
        print_status "Python environment synchronized successfully"
        print_status "Virtual environment: .venv"
        print_status "Dependencies: installed from pyproject.toml"
        print_status "Dev dependencies: included"
    else
        print_error "Failed to sync Python environment"
        exit 1
    fi
}


# Display connection information
show_connection_info() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "==============================="
    echo ""
    echo "📊 Database Information:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: product_reviews"
    echo "  Username: postgres"
    echo "  Password: password"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Python environment: ✅ Already set up with uv"
    echo "  2. Start the API server: uv run python main.py"
    echo "  3. Access API docs: http://localhost:8001/docs"
    echo "  4. Health check: http://localhost:8001/health"
    echo ""
    echo "🔧 Docker Commands:"
    echo "  Stop containers: $DOCKER_COMPOSE_CMD down"
    echo "  View logs: $DOCKER_COMPOSE_CMD logs postgres"
    echo "  Connect to DB: $DOCKER_COMPOSE_CMD exec postgres psql -U postgres product_reviews"
    echo ""
    echo "📦 uv Commands:"
    echo "  Run API: uv run python main.py"
    echo "  Add users: uv run python setup_users.py"
    echo "  Run tests: uv run pytest"
    echo "  Install package: uv pip install package-name"
    echo ""
    echo "📝 Environment file created: .env"
    echo ""
}

# Create .env file
create_env_file() {
    print_info "Creating .env file..."
    cat > .env << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=product_reviews
DB_USER=postgres
DB_PASSWORD=password

# FastAPI Configuration
APP_TITLE=Product Reviews API
APP_VERSION=1.0.0
DEBUG=true
API_PREFIX=/api/v1

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
EOF
    print_status ".env file created"
}

# Main execution
main() {
    echo ""
    check_docker
    check_docker_compose
    check_uv
    echo ""
    
    # Ask user if they want to clean up first
    echo ""
    echo -n "Do you want to stop existing containers? (y/N) [data will be preserved]: "
    read -r cleanup_response
    if [[ $cleanup_response =~ ^[Yy]$ ]]; then
        cleanup
        echo ""
    else
        print_info "Skipping cleanup"
        echo ""
    fi
    
    start_database
    echo ""
    run_migrations
    echo ""
    create_env_file
    echo ""
    
    # Set up Python environment first
    setup_python_env
    
    # Insert sample users using uv environment
    print_info "Inserting sample users with uv environment..."
    if uv run python setup_users.py; then
        print_status "Sample users inserted successfully"
    else
        print_warning "Failed to insert sample users. You can run 'uv run python setup_users.py' later."
    fi
    
    show_connection_info
}

# Run main function
main

