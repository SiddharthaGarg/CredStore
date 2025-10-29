"""Sample test file to demonstrate API testing."""

import pytest
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

# Sample UUIDs for testing
SAMPLE_PRODUCT_ID = str(uuid4())
SAMPLE_USER_ID = str(uuid4())
SAMPLE_REVIEW_ID = str(uuid4())


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


def test_create_review():
    """Test creating a review."""
    review_data = {
        "user_id": SAMPLE_USER_ID,
        "rating": 5,
        "description": "Great product!"
    }
    
    response = client.post(
        f"/api/v1/reviews/{SAMPLE_PRODUCT_ID}",
        json=review_data
    )
    
    # Note: This will fail without proper database setup and user creation
    # This is just a sample of how tests would be structured
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


def test_get_reviews():
    """Test getting reviews for a product."""
    response = client.get(f"/api/v1/reviews/{SAMPLE_PRODUCT_ID}")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


def test_get_review_metrics():
    """Test getting review metrics."""
    response = client.get(f"/api/v1/reviews/{SAMPLE_PRODUCT_ID}/metrics")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")


def test_invalid_uuid():
    """Test with invalid UUID format."""
    response = client.get("/api/v1/reviews/invalid-uuid")
    assert response.status_code in [400, 422]  # Should return validation error


if __name__ == "__main__":
    # Run sample tests
    print("Running sample API tests...")
    
    print("\n1. Testing root endpoint...")
    test_root_endpoint()
    
    print("\n2. Testing health check...")
    test_health_check()
    
    print("\n3. Testing invalid UUID...")
    test_invalid_uuid()
    
    print("\n4. Testing get reviews...")
    test_get_reviews()
    
    print("\n5. Testing get metrics...")
    test_get_review_metrics()
    
    print("\nSample tests completed!")
    print("\nNote: Some tests may fail due to missing database setup.")
    print("Set up PostgreSQL and create sample users to run full tests.")

