# 🚀 Product Reviews API - Complete Setup with Liquibase & Docker

## ⚡ Follow Quick Start (Recommended) from attached QUICK_START.md file

OR 

**One-command setup** - runs Docker, migrations, creates Python environment, and inserts sample users:

## Prerequisites
- Python 3.11+
- Docker
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

```bash
chmod +x setup.sh && ./setup.sh
# If you get Docker permission errors, run with sudo:
# sudo ./setup.sh
```

**That's it!** The script will:
- ✅ Check and validate uv installation
- ✅ Start PostgreSQL in Docker
- ✅ Run Liquibase migrations to create all tables
- ✅ Create Python virtual environment with uv
- ✅ Install all dependencies with uv
- ✅ Insert sample users for testing  
- ✅ Create `.env` configuration file

Then start the API:
```bash
uv run  python main.py
```

Visit: http://localhost:8001/docs

## 📋 What You Get

### 📦 **Modern Python Setup with uv**
- Fast virtual environment creation with uv
- Automatic dependency resolution and installation
- pyproject.toml-based dependency management
- Development dependencies included (pytest, httpx)

### 🐳 **Docker Setup**
- PostgreSQL 15 container with health checks
- Liquibase container for migrations
- Network isolation and volume persistence
- Easy cleanup and reset commands

### 🗄️ **Professional Database Management**
- **Liquibase migrations** for version-controlled schema changes
- **Rollback capabilities** for safe deployments
- **Constraint validation** (ratings 1-5, foreign keys, etc.)
- **Performance indexes** on commonly queried fields
- **Check constraints** for data integrity

### 👥 **Sample Data**
- 6 sample users with varied profiles
- UUIDs ready for API testing
- Real-world example data structure

### 🔧 **Production-Ready Configuration**
- Environment-based configuration with uv
- Health check endpoints
- Comprehensive error handling
- Connection pooling and management
- Fast dependency management with uv

## 📁 Project Structure

```
product_reviews/
├── 🐳 Docker & Migrations
│   ├── docker-compose.yml           # PostgreSQL + Liquibase services
│   ├── liquibase.properties         # Database connection config
│   └── migrations/                  # Liquibase migration files
│       ├── db.changelog-master.xml  # Master changelog
│       ├── 01-create-users-table.xml
│       ├── 02-create-reviews-table.xml
│       ├── 03-create-comments-table.xml
│       ├── 04-create-review-metrics-table.xml
│       └── 05-create-indexes.xml
│
├── 🔧 Setup Scripts
│   ├── setup.sh                    # Automated setup with uv (RECOMMENDED)
│   ├── setup_users.py              # Insert sample users
│
├── 🏗️ Application Code
│   ├── main.py                     # FastAPI application
│   ├── models.py                   # Database models (Peewee)
│   ├── schemas.py                  # API request/response schemas
│   ├── database.py                 # Connection management
│   ├── config.py                   # Configuration settings
│   ├── services/                   # Business logic layer
│   └── routers/                    # API endpoints
│
└── 📖 Documentation
    ├── LIQUIBASE_SETUP.md          # Detailed Liquibase guide
    ├── API_README.md               # API documentation
    ├── QUICK_START.md              # Quick start guide
    └── pyproject.toml              # Python dependencies (uv format)
```


## 🧪 Testing Your Setup

```bash
# Health check
curl http://localhost:8001/health

# Create a review (use user ID from setup output)
curl -X POST "http://localhost:8001/api/v1/reviews/$(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USER_ID_HERE", "rating": 5, "description": "Great!"}'

# Get review metrics
curl "http://localhost:8001/api/v1/reviews/PRODUCT_ID/metrics" | jq
```

## 🐛 Troubleshooting

### Database Issues
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset everything
docker-compose down -v && ./setup.sh
# If you get Docker permission errors:
# sudo docker-compose down -v && sudo ./setup.sh
```

### Migration Issues
```bash
# Validate migrations
docker-compose run --rm liquibase validate

# Check migration status
docker-compose run --rm liquibase status
```

### Python Issues
```bash
# Check database connection
uv run python -c "from models import check_tables_exist; print('✅ OK' if check_tables_exist() else '❌ Tables missing')"

# Reinstall dependencies
uv sync --force
```

## 💡 Key Benefits of This Setup

✅ **Modern Python Tooling**: Fast dependency management with uv  
✅ **Version-Controlled Schema**: All database changes tracked in git  
✅ **Safe Deployments**: Rollback capabilities for production  
✅ **Docker Isolation**: No local PostgreSQL installation needed  
✅ **One-Command Setup**: `./setup.sh` gets everything running (use `sudo ./setup.sh` if Docker permission issues)  
✅ **Production Ready**: Health checks, proper error handling  
✅ **Sample Data**: Ready-to-test with realistic data  
✅ **Clean Architecture**: SOLID principles, separated concerns  

## 🚀 Next Steps

1. **API Development**: Add your business logic to `services/`
2. **Frontend Integration**: Use the RESTful endpoints 
3. **Production Deployment**: Configure environment variables
4. **Monitoring**: Set up logging and health check monitoring
5. **Testing**: Run tests with `uv run pytest`

**Happy coding! 🎉**

