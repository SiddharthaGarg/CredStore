# Integration Tests

This directory contains integration tests for the homepage module API endpoints.

## Test Structure

The test structure is organized as follows:
- `tests/unit/` - Unit tests with mocked dependencies
- `tests/integration/` - Integration tests with real database connections

## Test Environment

Integration tests use separate test databases to ensure isolation from development/production data:

- **MongoDB**: Uses `appstore_test` database (configurable via `TEST_MONGODB_DATABASE`)
- **Elasticsearch**: Uses `products_test` index (configurable via `TEST_ELASTICSEARCH_INDEX`)

## Environment Variables

Set these environment variables to configure test databases:

```bash
TEST_MONGODB_URL=mongodb://localhost:27017
TEST_MONGODB_DATABASE=appstore_test
TEST_MONGODB_COLLECTION=products_test
TEST_ELASTICSEARCH_URL=http://localhost:9200
TEST_ELASTICSEARCH_INDEX=products_test
```

If not set, defaults will be used (with `_test` suffix).

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run with coverage
pytest tests/integration/ --cov=services --cov-report=html

# Run specific test file
pytest tests/integration/test_products_api.py
```

## Test Isolation

- Each test runs in isolation
- Test data is automatically cleaned up after each test
- Test databases are cleaned up after the test session
- No data persists between test runs

## Prerequisites

1. MongoDB and Elasticsearch must be running (can use docker-compose)
2. Test databases will be created automatically
3. Test data will be cleaned up automatically

