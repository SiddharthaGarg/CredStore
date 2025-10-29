# Quick Start Guide - Product Reviews API

## Prerequisites
- Python 3.11+
- PostgreSQL 12+ (or use Docker)
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

## Setup Instructions

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies
```bash
# Create virtual environment and install all dependencies in one command
uv sync
```

### 3. Database Setup (Option A: Docker - Recommended)
```bash
# Start PostgreSQL in Docker and run migrations
docker-compose up -d postgres
docker-compose run --rm liquibase
```

### 3. Database Setup (Option B: Local PostgreSQL)
```bash
# Create PostgreSQL database
createdb product_reviews

# Or using psql:
psql -c "CREATE DATABASE product_reviews;"
```

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env file with your database credentials (if using local PostgreSQL)
```

### 5. Initialize Database with Sample Users
```bash
uv run python setup_users.py
```

### 6. Run the API
```bash
uv run python main.py
```

The API will be available at:
- **API Base**: http://localhost:8001
- **Interactive Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## Quick Test

### Test the API

```Getting Sample Data

Product ID - Use product ID from list products api output in homepage module 
User ID - 
    1. Run ```bash python setup_user.py``` to see the list of users OR
    2. query in table by connecting to database - ```bash sudo docker-compose exec postgres psql -U postgres -d product_reviews```

```


```bash
# Get health status
curl http://localhost:8001/health

# Get reviews for a product 
curl "http://localhost:8001/api/v1/reviews/PRODUCT_ID"

# Get review metrics
curl "http://localhost:8001/api/v1/reviews/PRODUCT_ID/metrics"


# Add review

```

### Run Sample Tests
```bash
uv run python test_sample.py

# Or run full test suite
uv run pytest
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reviews/{product_id}/metrics` | Get rating distribution |
| GET | `/api/v1/reviews/{product_id}` | List product reviews |
| POST | `/api/v1/reviews/{product_id}` | Add new review |
| PUT | `/api/v1/reviews/{review_id}` | Update review |
| DELETE | `/api/v1/reviews/{review_id}` | Delete review |
| POST | `/api/v1/reviews/{review_id}/comments` | Add comment |
| GET | `/api/v1/reviews/{review_id}/comments` | List comments |

## Project Structure

```
product_reviews/
├── config.py              # Configuration
├── database.py            # Database connection
├── models.py              # Database models (Peewee)
├── schemas.py             # API schemas (Pydantic)
├── main.py                # FastAPI application
├── setup_users.py         # User setup script
├── setup.sh               # Automated setup script
├── test_sample.py         # Sample tests
├── pyproject.toml         # Dependencies (uv format)
├── docker-compose.yml     # Docker setup
├── liquibase.properties   # Liquibase config
├── migrations/            # Liquibase migration files
├── services/              # Business logic layer
│   ├── base_service.py    # Base service class
│   ├── review_service.py  # Review operations
│   ├── comment_service.py # Comment operations
│   └── metrics_service.py # Analytics
├── routers/               # API endpoints
│   └── reviews.py         # Reviews router
├── .env.example          # Environment template
└── README files          # Documentation
```

## Architecture Highlights

✅ **Modern Tooling**: Fast dependency management with uv  
✅ **SOLID Principles**: Clear separation of concerns  
✅ **Service Layer**: Business logic separated from API layer  
✅ **Error Handling**: Comprehensive error responses  
✅ **Validation**: Pydantic schemas for request/response validation  
✅ **Database**: PostgreSQL with Peewee ORM + Liquibase migrations  
✅ **Pagination**: Built-in pagination support  
✅ **Health Checks**: Monitoring endpoints  
✅ **Docker**: Containerized database and migrations  

## Need Help?

- Check the interactive API docs at `/docs`
- Review the full API documentation in `API_README.md`
- Use `SETUP_README.md` for detailed setup instructions
- Use `LIQUIBASE_SETUP.md` for database migration help
- Check application logs for debugging
- Verify database connection with health endpoint

## uv Commands Reference

```bash
# Create virtual environment and install all dependencies
uv sync

# Run application
uv run python main.py

# Run tests
uv run pytest

# Add new dependency
uv add package-name

# Update dependencies (sync with pyproject.toml)
uv sync
```

