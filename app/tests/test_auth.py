import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base
from app.api.deps import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

class TestAuthRegistration:
    """Test account registration"""
    
    def test_register_success(self):
        """Test successful registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "securepassword123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "user@example.com"
        assert float(data["balance"]) == 0.0
        assert data["status"] == "active"
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        email = "user@example.com"
        password = "securepassword123"
        
        # Register first
        client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        
        # Try to register same email again
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123"
            }
        )
        assert response.status_code == 422

class TestAuthLogin:
    """Test account authentication"""
    
    def test_login_success(self):
        """Test successful login"""
        # Register first
        email = "user@example.com"
        password = "securepassword123"
        
        client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"}
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # Register
        email = "user@example.com"
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correctpassword"}
        )
        
        # Try login with wrong password
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
