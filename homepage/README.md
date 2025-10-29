# App Store Homepage API

A FastAPI-based backend service for an App Store-like homepage module with MongoDB and Elasticsearch integration.

## Features

- **Product Management**: Add, list, update, and delete products
- **Search Functionality**: Full-text search powered by Elasticsearch
- **Pagination**: Efficient pagination for product listings
- **Category Filtering**: Filter products by category
- **MongoDB Storage**: Reliable product data storage
- **RESTful API**: Clean and well-documented API endpoints

## Prerequisites
- Python 3.11+
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager

## Initial Project Setup
**Install python3.13  and UV (package manager)**


## Quick Start with Docker


1. **Start the databases**:
   ```bash
   docker-compose up -d
   # Run with sudo if facing permission issues
   ```



2. **Create environment configuration**:
   ```bash
   # Create a .env file with these contents:
   cat > .env << 'EOF'
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DATABASE=appstore
   MONGODB_COLLECTION=products
   ELASTICSEARCH_URL=http://localhost:9200
   ELASTICSEARCH_INDEX=products
   APP_TITLE=App Store Homepage API
   APP_VERSION=1.0.0
   DEBUG=true
   EOF
   ```

3. **Activate Virtual Env** ( Optional if running main.py with UV command):
   ```bash
   # Create virtual env and install dependencies
   uv sync

   # Activate virtual venv 
   source .venv/bin/activate
   ```

4. **Run the API server**:
   ```bash
   uv run  python main.py
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Manual Setup

### 1. Install MongoDB

**On Ubuntu/Debian:**
```bash
# Import MongoDB GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2. Install Elasticsearch

**On Ubuntu/Debian:**
```bash
# Import Elasticsearch GPG key
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

# Add Elasticsearch repository
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Install Elasticsearch
sudo apt-get update
sudo apt-get install elasticsearch

# Configure Elasticsearch (disable security for local development)
echo "xpack.security.enabled: false" | sudo tee -a /etc/elasticsearch/elasticsearch.yml
echo "discovery.type: single-node" | sudo tee -a /etc/elasticsearch/elasticsearch.yml

# Start Elasticsearch service
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

### 3. Run Python Server

```bash
uv run --active python main.py
```

### 4. Configure Environment

Create a `.env` file in the project root with the database connection settings (see the Docker section above for the template).

### 5. Run the Application

```bash
python main.py
```

## API Endpoints

### Admin Endpoints

- **POST /admin/products** - Add a new product
- **PUT /admin/products/{product_id}** - Update a product
- **DELETE /admin/products/{product_id}** - Delete a product

### Public Endpoints

- **GET /products** - List products with pagination
- **GET /products/{product_id}** - Get a specific product
- **GET /products/search** - Search products
- **GET /health** - Health check

### Example Usage

#### Add a Product

```bash
curl -X POST "http://localhost:8000/admin/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amazing App",
    "description": "An amazing mobile application",
    "developer": "Tech Corp",
    "category": "Productivity",
    "price": 9.99,
    "version": "1.0.0",
    "tags": ["productivity", "utility", "mobile"]
  }'
```

#### List Products

```bash
curl "http://localhost:8000/products?page=1&page_size=10&category=Productivity"
```

#### Search Products

```bash
curl "http://localhost:8000/products/search?q=amazing%20app&page=1&page_size=10"
```

## Development

### Project Structure

```
homepage/
├── main.py              # FastAPI application
├── models.py            # Pydantic models and schemas
├── database.py          # Database connections and operations
├── config.py            # Configuration management
├── docker-compose.yml   # Docker services
└── pyproject.toml       # Project dependencies
```

### Running Tests

#### Unit Tests

```bash
# Install test dependencies
uv sync --extra dev

# Run unit tests with coverage report
pytest tests/unit/ --cov=services --cov-report=html

# View coverage report
# Open htmlcov/index.html in your browser
```

#### Integration Tests

```bash
# Ensure MongoDB and Elasticsearch are running
docker-compose up -d

# Set test environment variables (optional, defaults work)
export TEST_MONGODB_DATABASE=appstore_test
export TEST_ELASTICSEARCH_INDEX=products_test

# Run integration tests
pytest tests/integration/

# Run integration tests with coverage
pytest tests/integration/ --cov=services --cov-report=html
```

**Note**: Integration tests use separate test databases to ensure isolation from development data.

## Configuration Options

All configuration can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `appstore` | Database name |
| `MONGODB_COLLECTION` | `products` | Collection name for products |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch URL |
| `ELASTICSEARCH_INDEX` | `products` | Elasticsearch index name |
| `APP_TITLE` | `App Store Homepage API` | API title |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `true` | Enable debug mode |

## API Documentation

When the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
