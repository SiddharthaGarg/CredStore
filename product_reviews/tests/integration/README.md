# Integration Tests for Product Reviews Module

Integration tests for the Product Reviews API endpoints that test the complete flow from API to database.

## Setup

### Prerequisites

1. **PostgreSQL Database** must be running
2. **Test Database** must exist: `product_reviews_test`
3. **Liquibase Migrations** must be run on the test database

### Creating Test Database

If the test database doesn't exist, create it using one of these methods:

#### Method 1: Using psql (recommended)
```bash
# Connect to PostgreSQL (if using Docker)
sudo docker-compose exec postgres psql -U postgres

# Or connect directly if PostgreSQL is running locally
psql -U postgres -h localhost

# Then run:
CREATE DATABASE product_reviews_test;

# Exit psql
\q
```

#### Method 2: Using command line
```bash
# If using Docker
sudo docker-compose exec postgres psql -U postgres -c "CREATE DATABASE product_reviews_test;"

# Or if PostgreSQL is running locally
psql -U postgres -h localhost -c "CREATE DATABASE product_reviews_test;"
```

### Running Migrations on Test Database


**Manual Method**: After creating the test database, run Liquibase migrations:

```bash
# From product_reviews directory
docker run --rm \
  --network product_reviews_product_reviews_network \
  -v "$(pwd)/db/migrations:/liquibase/changelog:Z" \
  liquibase/liquibase:4.24 \
  --url=jdbc:postgresql://product_reviews_db:5432/product_reviews_test \
  --username=postgres \
  --password=password \
  --changeLogFile=changelog/db.changelog-master.xml \
  update
```

### Test Environment

The integration tests use a separate test database (`product_reviews_test`) configured via `.env.test` file to avoid affecting production data.

**Key Settings:**
- Test database is isolated with `_test` suffix
- Database is cleaned before and after each test
- Product validator is mocked to avoid MongoDB dependency
- Test users are created and cleaned up automatically

## Running Tests

### Run all integration tests:
```bash
# From product_reviews directory
uv run pytest tests/integration/ -v
```

### Run specific test class:
```bash
uv run pytest tests/integration/test_reviews_api.py::TestAddReview -v
```

### Run specific test:
```bash
uv run pytest tests/integration/test_reviews_api.py::TestAddReview::test_add_review_success -v
```

### Run with coverage:
```bash
uv run pytest tests/integration/ --cov=services --cov-report=html
```

## Test Coverage

The integration tests cover the following success scenarios:

1. **Add Review** (`TestAddReview`)
   - ✅ `test_add_review_success` - Successful review creation

2. **Update Review** (`TestUpdateReview`)
   - ✅ `test_update_review_success` - Successful review update

3. **List Reviews** (`TestListReviews`)
   - ✅ `test_list_reviews_success_empty` - List when no reviews exist
   - ✅ `test_list_reviews_success_with_data` - List with existing reviews
   - ✅ `test_list_reviews_with_pagination` - Pagination support

4. **Delete Review** (`TestDeleteReview`)
   - ✅ `test_delete_review_success` - Successful review deletion
   - ✅ `test_delete_review_removes_comments` - CASCADE delete verification

## Test Fixtures

- `test_db_manager`: Creates and manages database connection for tests
- `test_user`: Creates a test user for review operations
- `test_product_id`: Provides a mock product ID
- `client`: HTTP test client for API calls

## Database Cleanup

Tests automatically clean up:
- Reviews
- Comments (via CASCADE when review is deleted)
- Review Metrics (via CASCADE when review is deleted)
- Users

Each test runs in isolation with a clean database state.

