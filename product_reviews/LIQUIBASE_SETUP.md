# Liquibase + Docker Setup Guide

This guide explains how to set up the Product Reviews API using **Liquibase migrations** and **Docker** for database management.

## 🚀 Quick Start (Automated)

The easiest way to get everything running:

```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
# If you get Docker permission errors, run with sudo:
# sudo ./setup.sh
```

This script will:
- ✅ Start PostgreSQL in Docker
- ✅ Run Liquibase migrations to create tables
- ✅ Insert sample users for testing
- ✅ Create `.env` configuration file

## 📋 Manual Setup (Step by Step)

### 1. Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.11+** for running the API
- **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** (if cloning the repository)

### 2. Start PostgreSQL Database

```bash
# Start only the PostgreSQL container
docker-compose up -d postgres

# Wait for database to be ready
docker-compose logs -f postgres
```

### 3. Run Liquibase Migrations

```bash
# Run all migrations to create tables and indexes
docker-compose run --rm liquibase

# Alternative: Run specific migration
docker-compose run --rm liquibase --changelog-file=/liquibase/changelog/01-create-users-table.xml update
```

### 4. Verify Database Schema

```bash
# Connect to database to verify tables
docker-compose exec postgres psql -U postgres product_reviews

# List all tables
\dt

# Check users table structure
\d users

# Exit psql
\q
```

### 5. Set up Python Environment

```bash
# Create virtual environment and install all dependencies
uv sync
```

### 6. Insert Sample Users

```bash
# Option 1: Using Python script with uv (recommended)
uv run python setup_users.py

# Option 2: Using Docker exec
docker-compose exec postgres psql -U postgres product_reviews -c "
INSERT INTO users (id, name, email, profile) VALUES 
('$(uuidgen)', 'John Doe', 'john@example.com', 'https://example.com/john.jpg'),
('$(uuidgen)', 'Jane Smith', 'jane@example.com', null);
"
```

### 7. Start the API

```bash
# Create .env file (if not created by setup script)
cp .env.example .env

# Start the FastAPI server with uv
uv run python main.py
```

## 📁 Liquibase Migration Files

The migration files are located in the `migrations/` directory:

```
migrations/
├── db.changelog-master.xml      # Master changelog that includes all migrations
├── 01-create-users-table.xml    # Users table with constraints
├── 02-create-reviews-table.xml  # Reviews table with foreign keys
├── 03-create-comments-table.xml # Comments table with relationships
├── 04-create-review-metrics-table.xml # Metrics table for upvotes/downvotes
└── 05-create-indexes.xml        # Performance indexes
```

## 🗃️ Database Schema

The migrations create the following schema:

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    profile TEXT
);
```

### Reviews Table
```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    UNIQUE(user_id, product_id)
);
```

### Comments Table
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY,
    review_id UUID NOT NULL REFERENCES reviews(id),
    user_id UUID NOT NULL REFERENCES users(id),
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### Review Metrics Table
```sql
CREATE TABLE review_metrics (
    id UUID PRIMARY KEY,
    review_id UUID UNIQUE NOT NULL REFERENCES reviews(id),
    upvotes INTEGER DEFAULT 0 CHECK (upvotes >= 0),
    downvotes INTEGER DEFAULT 0 CHECK (downvotes >= 0),
    comments_count INTEGER DEFAULT 0 CHECK (comments_count >= 0)
);
```

## 🔧 Liquibase Commands

### Common Operations

```bash
# Update database to latest version
docker-compose run --rm liquibase update

# Show pending changes
docker-compose run --rm liquibase status

# Generate SQL for review (don't execute)
docker-compose run --rm liquibase updateSQL

# Rollback last changeset
docker-compose run --rm liquibase rollbackCount 1

# Rollback to specific tag
docker-compose run --rm liquibase rollback v1.0

# Validate changelog
docker-compose run --rm liquibase validate
```

### Database Information

```bash
# List all applied changesets
docker-compose run --rm liquibase history

# Show database documentation
docker-compose run --rm liquibase dbDoc /tmp/docs

# Generate changelog from existing database
docker-compose run --rm liquibase generateChangeLog
```

## 🐳 Docker Commands

### Container Management

```bash
# Start all services
docker-compose up -d

# Start only database
docker-compose up -d postgres

# Stop all services
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# View logs
docker-compose logs postgres
docker-compose logs liquibase
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres product_reviews

# Run SQL file
docker-compose exec -T postgres psql -U postgres product_reviews < backup.sql

# Create database backup
docker-compose exec postgres pg_dump -U postgres product_reviews > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres product_reviews < backup.sql
```

## 🧪 Testing the Setup

### Verify Database

```bash
# Check database connection with uv
uv run python -c "
from config import settings
import psycopg2
try:
    conn = psycopg2.connect(settings.database_url)
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Check API health
curl http://localhost:8001/health
```

### Test API Endpoints

```bash
# Get all users (should show sample users)
curl "http://localhost:8001/api/v1/reviews/$(uuidgen)" | jq

# Get review metrics for non-existent product (should return empty metrics)
curl "http://localhost:8001/api/v1/reviews/$(uuidgen)/metrics" | jq
```

## 🚨 Troubleshooting

### Common Issues

1. **PostgreSQL not starting**
   ```bash
   # Check Docker logs
   docker-compose logs postgres
   
   # Ensure port 5432 is not in use
   lsof -i :5432
   ```

2. **Liquibase migration fails**
   ```bash
   # Check migration syntax
   docker-compose run --rm liquibase validate
   
   # View detailed logs
   docker-compose run --rm liquibase --log-level=DEBUG update
   ```

3. **Python can't connect to database**
   ```bash
   # Verify database is running
   docker-compose ps
   
   # Check connection from container
   docker-compose exec postgres pg_isready -U postgres
   ```

4. **API returns 500 errors**
   ```bash
   # Check if tables exist
   uv run python -c "from models import check_tables_exist; print(check_tables_exist())"
   
   # Verify sample users exist
   uv run python setup_users.py
   ```

### Reset Everything

```bash
# Nuclear option: reset everything
docker-compose down -v
docker system prune -f
./setup.sh
# If you get Docker permission errors:
# sudo docker-compose down -v && sudo docker system prune -f && sudo ./setup.sh
```

## 🎯 Production Considerations

### Security
- Change default PostgreSQL password
- Use environment variables for secrets
- Enable SSL for database connections
- Restrict Docker network access

### Performance
- Configure PostgreSQL memory settings
- Monitor Liquibase changeset performance
- Use connection pooling in production

### Monitoring
- Set up health checks for containers
- Monitor database disk usage
- Log migration execution times

### Backup Strategy
- Regular automated database backups
- Test backup restoration procedures
- Version control for migration files

