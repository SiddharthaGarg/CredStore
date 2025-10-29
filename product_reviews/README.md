# Product Reviews API - Setup Guide

FastAPI-based product reviews system with PostgreSQL, Peewee ORM, and Docker.

## Quick Start (Recommended)

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager

### One-Command Setup
```bash
chmod +x setup.sh && ./setup.sh
# If you get Docker permission errors, run with sudo:
# sudo ./setup.sh
```

This automatically:
- ✅ Starts PostgreSQL in Docker
- ✅ Runs database migrations
- ✅ Creates Python virtual environment
- ✅ Installs dependencies
- ✅ Inserts sample users

### Start API
```bash
# Create virtual env and install dependencies
uv sync 

# Activate virtual env
source .venv/bin/activate

# Start fast api server
uv run python main.py
```

API available at: http://localhost:8001/docs

## Play with API's


### Getting Sample Data

Product ID - Use product ID from list products api output in homepage module 
User ID - 
    1. Run ```bash python setup_user.py``` to see the list of users 
    2. Query in table by connecting to database - ```bash sudo docker-compose exec postgres psql -U postgres -d product_reviews```


### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reviews/{product_id}/metrics` | Get review metrics (total, avg rating, distribution) |
| GET | `/api/v1/reviews/{product_id}` | List product reviews (paginated) |
| POST | `/api/v1/reviews/{product_id}` | Add new review |
| PUT | `/api/v1/reviews/{review_id}` | Update review |
| DELETE | `/api/v1/reviews/{review_id}` | Delete review |
| GET | `/api/v1/reviews/{review_id}` | Get review details |
| POST | `/api/v1/reviews/{review_id}/comments` | Add comment |
| GET | `/api/v1/reviews/{review_id}/comments` | List comments (paginated) |
| GET | `/health` | Health check |


## Manual Setup

### 1. Start Database
```bash
docker-compose up -d postgres
```

### 2. Run Migrations
```bash
docker-compose run --rm liquibase
```

### 3. Install Dependencies
```bash
uv sync
```

### 4. Setup Environment
```bash
cp .env.example .env
```

### 5. Insert Sample Users
```bash
uv run python setup_users.py
```

### 6. Run API
```bash
uv run python main.py
```


## Project Structure

```
product_reviews/
├── db/
│   ├── models/        # Database models
│   ├── dao/          # Data access objects
│   ├── migrations/   # Liquibase migrations
│   └── manager.py    # Database connection
├── services/         # Business logic
├── api/             # API layer (routers, schemas)
├── events/          # Event bus system
├── main.py          # FastAPI app
├── config.py        # Configuration
└── setup.sh         # Automated setup script
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Reset database
docker-compose down -v && ./setup.sh
```

### Migration Issues
```bash
# Validate migrations
docker-compose run --rm liquibase validate

# Check status
docker-compose run --rm liquibase status
```

### Python Environment
```bash
# Reinstall dependencies
uv sync --force

# Verify database tables
uv run python -c "from db.models import check_tables_exist; print(check_tables_exist())"
```

## Testing

```bash
# Health check
curl http://localhost:8001/health

# Get review metrics
curl "http://localhost:8001/api/v1/reviews/PRODUCT_ID/metrics"

# Add review (use user ID from setup_users.py output)
curl -X POST "http://localhost:8001/api/v1/reviews/PRODUCT_ID" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID", "rating": 5, "description": "Great product!"}'
```

## Configuration

Key environment variables (`.env`):
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: product_reviews)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: password)

## Features

- **SOLID Architecture**: Clear separation of concerns
- **Docker Setup**: Easy database management
- **Liquibase Migrations**: Version-controlled schema changes
- **Event-Driven**: Decoupled rating updates
- **Modern Tooling**: Fast dependency management with uv
