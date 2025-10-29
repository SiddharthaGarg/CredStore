# Product Reviews API

A comprehensive FastAPI-based product reviews system with PostgreSQL and Peewee ORM, built following SOLID design principles with clear separation of concerns.

## Features

- **Complete Review System**: Add, update, delete, and list product reviews
- **Comment System**: Add and manage comments on reviews  
- **Review Metrics**: Track upvotes, downvotes, and rating distributions
- **User Management**: Support for user profiles and associations
- **Pagination**: Built-in pagination for all list endpoints
- **Comprehensive Error Handling**: Structured error responses
- **Database Transactions**: ACID compliance with PostgreSQL
- **Clean Architecture**: Service layer, API layer, and database layer separation

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database
- **Peewee ORM**: Lightweight ORM for database operations
- **Pydantic**: Data validation and serialization
- **Docker**: Containerization support

## Architecture

The application follows SOLID principles with clear separation of concerns:

```
├── config.py          # Configuration management
├── database.py        # Database connection and utilities
├── models.py          # Database models (Peewee)
├── schemas.py         # API request/response schemas (Pydantic)
├── services/          # Business logic layer
│   ├── base_service.py      # Base service with common functionality
│   ├── review_service.py    # Review business logic
│   ├── comment_service.py   # Comment business logic
│   └── metrics_service.py   # Metrics and analytics
├── routers/           # API endpoints
│   └── reviews.py           # Review and comment endpoints
└── main.py            # FastAPI application entry point
```

## Database Schema

### User
- `id`: UUID (Primary Key)
- `name`: VARCHAR(255)
- `email`: VARCHAR(255) (Unique)
- `profile`: TEXT (S3 URL for profile image)

### Review
- `id`: UUID (Primary Key)
- `product_id`: UUID (Foreign Key to external product)
- `user_id`: UUID (Foreign Key to User)
- `rating`: INTEGER (1-5)
- `description`: VARCHAR(255)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP
- `status`: VARCHAR(20) ('active' or 'inactive')

### Comment
- `id`: UUID (Primary Key)
- `review_id`: UUID (Foreign Key to Review)
- `user_id`: UUID (Foreign Key to User)
- `description`: TEXT
- `created_at`: TIMESTAMP

### ReviewMetrics
- `id`: UUID (Primary Key)
- `review_id`: UUID (Foreign Key to Review, Unique)
- `upvotes`: INTEGER
- `downvotes`: INTEGER
- `comments_count`: INTEGER

## API Endpoints

### Review Metrics
- `GET /api/v1/reviews/{product_id}/metrics` - Get cumulative rating distribution

### Reviews
- `GET /api/v1/reviews/{product_id}` - List reviews for a product (paginated)
- `POST /api/v1/reviews/{product_id}` - Add a new review
- `PUT /api/v1/reviews/{review_id}` - Update a review
- `DELETE /api/v1/reviews/{review_id}` - Delete a review
- `GET /api/v1/reviews/{review_id}` - Get specific review details

### Comments
- `POST /api/v1/reviews/{review_id}/comments` - Add comment to a review
- `GET /api/v1/reviews/{review_id}/comments` - List comments for a review (paginated)

### System
- `GET /` - API information
- `GET /health` - Health check endpoint

## Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- pip or poetry

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd product_reviews
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your database configuration
   ```

4. **Create PostgreSQL database**:
   ```sql
   CREATE DATABASE product_reviews;
   CREATE USER reviews_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE product_reviews TO reviews_user;
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8001`

## Usage Examples

### Add a Review
```bash
curl -X POST "http://localhost:8001/api/v1/reviews/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "456e7890-e89b-12d3-a456-426614174000",
    "rating": 5,
    "description": "Excellent product! Highly recommended."
  }'
```

### Get Reviews for a Product
```bash
curl "http://localhost:8001/api/v1/reviews/123e4567-e89b-12d3-a456-426614174000?page=1&limit=10"
```

### Add Comment to Review
```bash
curl -X POST "http://localhost:8001/api/v1/reviews/review-uuid/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Great review! Thanks for sharing.",
    "user_id": "user-uuid"
  }'
```

### Get Rating Metrics
```bash
curl "http://localhost:8001/api/v1/reviews/123e4567-e89b-12d3-a456-426614174000/metrics"
```

## Response Format

All API responses follow a consistent format:

```json
{
  "data": {
    // Response data here
  },
  "err": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request`: Validation errors
- `404 Not Found`: Resource not found
- `403 Forbidden`: Permission errors  
- `422 Unprocessable Entity`: Request validation errors
- `500 Internal Server Error`: Server errors

