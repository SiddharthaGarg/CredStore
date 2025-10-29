"""Standalone script to insert sample users into the database.

This script works with uv virtual environments and can be run with:
    uv run python setup_users.py

The script will automatically use the configuration from config.py
and connect to the database specified in .env or environment variables.
"""

import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

def connect_to_database():
    """Create database connection."""
    try:
        # Import settings here to ensure it's loaded with proper environment
        from config import settings
        
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        try:
            from config import settings
            print(f"Connection details: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        except ImportError:
            print("Could not load configuration settings")
        return None

def insert_sample_users():
    """Insert sample users into the database."""
    
    print("🔄 Inserting sample users...")
    
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Sample users data
        sample_users = [
            {
                "id": str(uuid.uuid4()),
                "name": "John Doe",
                "email": "john.doe@example.com",
                "profile": "https://example.com/profiles/john.jpg"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Jane Smith", 
                "email": "jane.smith@example.com",
                "profile": "https://example.com/profiles/jane.jpg"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Bob Johnson",
                "email": "bob.johnson@example.com",
                "profile": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Alice Williams",
                "email": "alice.williams@example.com",
                "profile": "https://example.com/profiles/alice.jpg"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Charlie Brown",
                "email": "charlie.brown@example.com",
                "profile": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Diana Prince",
                "email": "diana.prince@example.com",
                "profile": "https://example.com/profiles/diana.jpg"
            }
        ]
        
        print(f"📝 Attempting to insert {len(sample_users)} users...")
        
        inserted_count = 0
        existing_count = 0
        
        # Insert users
        for user_data in sample_users:
            try:
                cursor.execute("""
                    INSERT INTO users (id, name, email, profile) 
                    VALUES (%(id)s, %(name)s, %(email)s, %(profile)s)
                    ON CONFLICT (email) DO NOTHING
                    RETURNING id
                """, user_data)
                
                if cursor.rowcount > 0:
                    print(f"✓ Created user: {user_data['name']} ({user_data['email']})")
                    inserted_count += 1
                else:
                    print(f"⚠ User {user_data['name']} already exists")
                    existing_count += 1
                    
            except Exception as e:
                print(f"✗ Error creating user {user_data['name']}: {e}")
        
        # Commit changes
        conn.commit()
        
        print(f"\n📊 Summary:")
        print(f"  • Users inserted: {inserted_count}")
        print(f"  • Users already existing: {existing_count}")
        
        # Display all users in database
        cursor.execute("SELECT id, name, email, profile FROM users ORDER BY name")
        users = cursor.fetchall()
        
        print(f"\n📋 Total users in database: {len(users)}")
        
        if users:
            print("\n👥 User List:")
            for user in users:
                profile_info = f" (Profile: {user['profile']})" if user['profile'] else " (No profile)"
                print(f"  • {user['name']} - {user['email']}")
                print(f"    ID: {user['id']}{profile_info}")
        
        # Show sample API commands
        if users:
            first_user_id = users[0]['id']
            sample_product_id = str(uuid.uuid4())
            
            print(f"\n🧪 Sample API Testing Commands:")
            print(f"# Create a review:")
            print(f'curl -X POST "http://localhost:8001/api/v1/reviews/{sample_product_id}" \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"user_id": "{first_user_id}", "rating": 5, "description": "Great product!"}}\'')
            
            print(f"\n# Get reviews for product:")
            print(f'curl "http://localhost:8001/api/v1/reviews/{sample_product_id}"')
            
            print(f"\n# Get review metrics:")
            print(f'curl "http://localhost:8001/api/v1/reviews/{sample_product_id}/metrics"')
        
        cursor.close()
        conn.close()
        
        print("\n✅ Sample users operation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during user insertion: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def check_database_connection():
    """Check if database is accessible."""
    print("🔍 Checking database connection...")
    
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Connected to PostgreSQL: {version}")
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        if table_exists:
            print("✓ Users table exists")
        else:
            print("❌ Users table does not exist. Please run migrations first.")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Main function."""
    print("👥 Product Reviews API - User Setup (uv compatible)")
    print("=================================================")
    
    # Check if we're running in a uv environment
    if os.environ.get('VIRTUAL_ENV') and 'uv' in os.environ.get('VIRTUAL_ENV', ''):
        print("✅ Running in uv virtual environment")
    elif os.path.exists('.venv'):
        print("ℹ️ .venv directory detected (likely uv environment)")
    else:
        print("⚠️ No virtual environment detected. Consider using: uv run python setup_users.py")
    
    if not check_database_connection():
        print("\n💡 Setup Instructions:")
        print("1. Ensure PostgreSQL is running: docker-compose up -d postgres")
        print("2. Run migrations: docker-compose run --rm liquibase")
        print("3. Set up Python environment: uv venv && uv pip install -e .")
        print("4. Try running this script again: uv run python setup_users.py")
        sys.exit(1)
    
    success = insert_sample_users()
    
    if success:
        print("\n🎉 User setup completed!")
        print("\n🚀 Next Steps:")
        print("1. Start the API: uv run python main.py")
        print("2. Visit API docs: http://localhost:8001/docs")
        print("3. Test endpoints using the sample commands above")
        print("\n📦 uv Commands:")
        print("- Run API: uv run python main.py")
        print("- Run tests: uv run pytest")
        print("- Add dependency: uv add package-name")
    else:
        print("\n❌ User setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

