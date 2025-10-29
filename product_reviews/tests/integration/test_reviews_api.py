"""Integration tests for Reviews API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from db.models import User


@pytest.mark.asyncio
class TestAddReview:
    """Integration tests for adding reviews."""
    
    async def test_add_review_success(
        self, client: AsyncClient, test_user, test_product_id
    ):
        """Test successful review creation."""
        review_data = {
            "user_id": str(test_user.id),
            "rating": 5,
            "description": "Excellent product! Highly recommended."
        }
        
        response = await client.post(
            f"/api/v1/reviews/{test_product_id}",
            json=review_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["err"] is None
        
        review = data["data"]
        assert review["id"] is not None
        assert review["user_details"]["id"] == str(test_user.id)
        assert review["user_details"]["name"] == test_user.name
        assert review["rating"] == review_data["rating"]
        assert review["description"] == review_data["description"]
        assert review["upvotes"] == 0
        assert review["downvotes"] == 0
        assert "created_at" in review
        assert "updated_at" in review
        assert "comments" in review


@pytest.mark.asyncio
class TestUpdateReview:
    """Integration tests for updating reviews."""
    
    async def test_update_review_success(
        self, client: AsyncClient, test_user, test_product_id
    ):
        """Test successful review update."""
        # First create a review
        create_data = {
            "user_id": str(test_user.id),
            "rating": 3,
            "description": "Average product"
        }
        
        create_response = await client.post(
            f"/api/v1/reviews/{test_product_id}",
            json=create_data
        )
        
        assert create_response.status_code == 201
        review_id = create_response.json()["data"]["id"]
        
        # Update the review
        update_data = {
            "rating": 5,
            "description": "Changed my mind, it's actually great!",
            "upvotes": 10,
            "downvotes": 2
        }
        
        response = await client.put(
            f"/api/v1/reviews/{review_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["err"] is None
        
        updated_review = data["data"]
        assert updated_review["id"] == review_id
        assert updated_review["rating"] == update_data["rating"]
        assert updated_review["description"] == update_data["description"]
        assert updated_review["upvotes"] == update_data["upvotes"]
        assert updated_review["downvotes"] == update_data["downvotes"]


@pytest.mark.asyncio
class TestListReviews:
    """Integration tests for listing reviews."""
    
    async def test_list_reviews_success_empty(
        self, client: AsyncClient, test_product_id
    ):
        """Test listing reviews when none exist."""
        response = await client.get(f"/api/v1/reviews/{test_product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["err"] is None
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0
    
    async def test_list_reviews_success_with_data(
        self, client: AsyncClient, test_db_manager, test_product_id
    ):
        """Test listing reviews with existing data."""
        
        users = []
        for i in range(3):
            user = User.create(
                id=uuid4(),
                name=f"Test User {i}",
                email=f"test_{uuid4()}@example.com",
                profile="https://example.com/profile.jpg"
            )
            users.append(user)
            
        reviews_data = [
            {
                "user_id": str(user.id),
                "rating": 5,
                "description": f"Great review {i}"
            }
            for i, user in enumerate(users)
        ]
        created_reviews = []
        for review_data in reviews_data:
            response = await client.post(
                f"/api/v1/reviews/{test_product_id}",
                json=review_data
            )
            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
            created_reviews.append(response.json()["data"]["id"])
        response = await client.get(f"/api/v1/reviews/{test_product_id}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["err"] is None
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 3
        review_ids = [review["id"] for review in data["data"]]
        for created_id in created_reviews:
            assert created_id in review_ids
    
    async def test_list_reviews_with_pagination(
        self, client: AsyncClient, test_db_manager, test_product_id
    ):
        """Test listing reviews with pagination."""
        users = []
        for i in range(5):
            user = User.create(
                id=uuid4(),
                name=f"Test User {i}",
                email=f"test_{uuid4()}@example.com",
                profile="https://example.com/profile.jpg"
            )
            users.append(user)
        for i, user in enumerate(users):
            review_data = {
                "user_id": str(user.id),
                "rating": 4,
                "description": f"Review {i+1}"
            }
            response = await client.post(
                f"/api/v1/reviews/{test_product_id}",
                json=review_data
            )
            assert response.status_code == 201
        response = await client.get(f"/api/v1/reviews/{test_product_id}", params={"page": 1, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        response = await client.get(f"/api/v1/reviews/{test_product_id}", params={"page": 2, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2


@pytest.mark.asyncio
class TestDeleteReview:
    """Integration tests for deleting reviews."""
    
    async def test_delete_review_success(
        self, client: AsyncClient, test_user, test_product_id
    ):
        """Test successful review deletion."""
        # Create a review
        create_data = {
            "user_id": str(test_user.id),
            "rating": 4,
            "description": "Good product"
        }
        
        create_response = await client.post(
            f"/api/v1/reviews/{test_product_id}",
            json=create_data
        )
        
        assert create_response.status_code == 201
        review_id = create_response.json()["data"]["id"]
        
        response = await client.delete(f"/api/v1/reviews/{review_id}")
        
        assert response.status_code == 204
        
        list_response = await client.get(f"/api/v1/reviews/{test_product_id}")
        assert list_response.status_code == 200
        reviews_data = list_response.json()["data"]
        review_ids = [review["id"] for review in reviews_data]
        assert review_id not in review_ids, "Deleted review should not appear in product reviews list"
    
    async def test_delete_review_removes_comments(
        self, client: AsyncClient, test_user, test_product_id
    ):
        """Test that deleting a review also removes associated comments."""
        create_data = {
            "user_id": str(test_user.id),
            "rating": 5,
            "description": "Great product"
        }
        
        create_response = await client.post(
            f"/api/v1/reviews/{test_product_id}",
            json=create_data
        )
        
        review_id = create_response.json()["data"]["id"]
        
        comment_data = {
            "user_id": str(test_user.id),
            "description": "I agree with this review!"
        }
        
        comment_response = await client.post(
            f"/api/v1/reviews/{review_id}/comments",
            json=comment_data
        )
        
        assert comment_response.status_code == 201
        
        comments_response = await client.get(
            f"/api/v1/reviews/{review_id}/comments"
        )
        assert comments_response.status_code == 200
        comments = comments_response.json()["data"]
        assert len(comments) == 1
        
        delete_response = await client.delete(f"/api/v1/reviews/{review_id}")
        assert delete_response.status_code == 204
        
        comments_response = await client.get(
            f"/api/v1/reviews/{review_id}/comments"
        )
        assert comments_response.status_code == 404  # Review doesn't exist

