#!/usr/bin/env python3
"""Simple test script to verify the API functionality."""

import asyncio
import json
import sys
from typing import Dict, Any

import httpx


async def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("Testing App Store Homepage API...")
        
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Status: {health_data.get('status')}")
                print(f"   MongoDB: {health_data.get('mongodb')}")
                print(f"   Elasticsearch: {health_data.get('elasticsearch')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Failed to connect: {e}")
            return False
        
        # Test adding a product
        print("\n2. Testing add product...")
        test_product = {
            "name": "Test Mobile App",
            "description": "A fantastic test application for mobile devices",
            "developer": "Test Developer Inc.",
            "category": "Productivity",
            "price": 4.99,
            "version": "1.0.0",
            "tags": ["productivity", "mobile", "test"]
        }
        
        try:
            response = await client.post(f"{base_url}/admin/products", json=test_product)
            print(f"Add product: {response.status_code}")
            if response.status_code == 201:
                product_data = response.json()
                product_id = product_data["id"]
                print(f"   Created product ID: {product_id}")
                print(f"   Product name: {product_data['name']}")
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"   Failed: {e}")
            return False
        
        # Test listing products
        print("\n3. Testing list products...")
        try:
            response = await client.get(f"{base_url}/products?page=1&page_size=10")
            print(f"List products: {response.status_code}")
            if response.status_code == 200:
                products_data = response.json()
                print(f"   Total products: {products_data['total']}")
                print(f"   Products on this page: {len(products_data['products'])}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # Test search
        print("\n4. Testing search products...")
        try:
            response = await client.get(f"{base_url}/products/search?q=test&page=1&page_size=10")
            print(f"Search products: {response.status_code}")
            if response.status_code == 200:
                search_data = response.json()
                print(f"   Search query: {search_data['query']}")
                print(f"   Results found: {search_data['total']}")
                print(f"   Search took: {search_data['took']}ms")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # Test get specific product
        print("\n5. Testing get product by ID...")
        try:
            response = await client.get(f"{base_url}/products/{product_id}")
            print(f"Get product: {response.status_code}")
            if response.status_code == 200:
                product_data = response.json()
                print(f"   Product: {product_data['name']} v{product_data['version']}")
                print(f"   Developer: {product_data['developer']}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        print("\n✅ API test completed successfully!")
        return True


def main():
    """Main function to run the tests."""
    print("App Store Homepage API Test Script")
    print("=" * 40)
    print("Make sure the API server is running on http://localhost:8000")
    print("You can start it with: python main.py")
    
    try:
        result = asyncio.run(test_api())
        if result:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
