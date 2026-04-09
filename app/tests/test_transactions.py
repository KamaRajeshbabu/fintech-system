import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base
from app.api.deps import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_txn.db"

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

@pytest.fixture
def auth_header():
    """Create and return authenticated user with token"""
    # Register user
    register_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert register_response.status_code == 201
    
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestTransactionCreation:
    """Test transaction creation"""
    
    def test_create_credit_transaction_success(self, auth_header):
        """Test successful credit transaction"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "credit",
                "idempotency_key": "txn-001",
                "description": "Salary deposit"
            },
            headers=auth_header
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["amount"]) == 100.0
        assert data["type"] == "credit"
        assert float(data["new_balance"]) == 100.0
        assert data["duplicate"] == False
    
    def test_create_debit_transaction_success(self, auth_header):
        """Test successful debit transaction after credit"""
        # First, credit account
        client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "credit",
                "idempotency_key": "txn-001"
            },
            headers=auth_header
        )
        
        # Then debit
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 30.00,
                "type": "debit",
                "idempotency_key": "txn-002"
            },
            headers=auth_header
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "debit"
        assert float(data["new_balance"]) == 70.0
    
    def test_debit_insufficient_balance(self, auth_header):
        """Test debit with insufficient balance"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 1000.00,
                "type": "debit",
                "idempotency_key": "txn-003"
            },
            headers=auth_header
        )
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]
    
    def test_negative_amount_rejected(self, auth_header):
        """Test that negative amounts are rejected"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": -100.00,
                "type": "credit",
                "idempotency_key": "txn-004"
            },
            headers=auth_header
        )
        assert response.status_code == 422
    
    def test_invalid_transaction_type(self, auth_header):
        """Test invalid transaction type"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "invalid",
                "idempotency_key": "txn-005"
            },
            headers=auth_header
        )
        assert response.status_code == 422
    
    def test_missing_idempotency_key(self, auth_header):
        """Test transaction without idempotency key"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "credit"
            },
            headers=auth_header
        )
        assert response.status_code == 422

class TestIdempotency:
    """Test idempotency handling"""
    
    def test_duplicate_transaction_idempotent(self, auth_header):
        """Test that duplicate idempotency keys return same result"""
        idempotency_key = "unique-txn-001"
        amount = 100.00
        
        # First request
        response1 = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": amount,
                "type": "credit",
                "idempotency_key": idempotency_key
            },
            headers=auth_header
        )
        assert response1.status_code == 201
        txn_id_1 = response1.json()["id"]
        dup_1 = response1.json()["duplicate"]
        
        # Retry with same key
        response2 = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": amount,
                "type": "credit",
                "idempotency_key": idempotency_key
            },
            headers=auth_header
        )
        assert response2.status_code == 201
        data = response2.json()
        assert data["duplicate"] == True
        assert data["id"] == txn_id_1  # Same transaction ID
    
    def test_multiple_credits_same_account(self, auth_header):
        """Test multiple transactions don't get duplicated"""
        # Multiple credits
        for i in range(3):
            response = client.post(
                "/api/transactions/",
                json={
                    "account_id": 1,
                    "amount": 100.00,
                    "type": "credit",
                    "idempotency_key": f"txn-{i:03d}"
                },
                headers=auth_header
            )
            assert response.status_code == 201
        
        # Check balance
        response = client.get("/api/transactions/balance", headers=auth_header)
        assert response.status_code == 200
        assert float(response.json()["current_balance"]) == 300.0

class TestTransactionHistory:
    """Test transaction history endpoints"""
    
    def test_get_balance(self, auth_header):
        """Test getting current balance"""
        # Add transaction
        client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 150.50,
                "type": "credit",
                "idempotency_key": "txn-balance-1"
            },
            headers=auth_header
        )
        
        response = client.get("/api/transactions/balance", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert float(data["current_balance"]) == 150.50
    
    def test_get_transaction_history(self, auth_header):
        """Test getting transaction history"""
        # Add multiple transactions
        for i in range(5):
            client.post(
                "/api/transactions/",
                json={
                    "account_id": 1,
                    "amount": 50.00,
                    "type": "credit",
                    "idempotency_key": f"txn-hist-{i:03d}"
                },
                headers=auth_header
            )
        
        response = client.get(
            "/api/transactions/history?limit=10&offset=0",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 5
        assert len(data["transactions"]) == 5
        assert float(data["current_balance"]) == 250.0
    
    def test_history_pagination(self, auth_header):
        """Test pagination in history"""
        # Add 10 transactions
        for i in range(10):
            client.post(
                "/api/transactions/",
                json={
                    "account_id": 1,
                    "amount": 10.00,
                    "type": "credit",
                    "idempotency_key": f"txn-page-{i:03d}"
                },
                headers=auth_header
            )
        
        # Get first page
        response = client.get(
            "/api/transactions/history?limit=5&offset=0",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5
        assert data["total_count"] == 10
        
        # Get second page
        response = client.get(
            "/api/transactions/history?limit=5&offset=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5

class TestSnapshots:
    """Test snapshot functionality"""
    
    def test_get_latest_snapshot(self, auth_header):
        """Test getting latest snapshot"""
        # Add transaction
        client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 200.00,
                "type": "credit",
                "idempotency_key": "txn-snap-1"
            },
            headers=auth_header
        )
        
        response = client.get(
            "/api/transactions/snapshot/latest",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 200.0
        assert data["transaction_count"] == 1
    
    def test_generate_snapshot(self, auth_header):
        """Test manually generating a snapshot"""
        # Add transactions
        for i in range(3):
            client.post(
                "/api/transactions/",
                json={
                    "account_id": 1,
                    "amount": 50.00,
                    "type": "credit",
                    "idempotency_key": f"txn-snap-{i}"
                },
                headers=auth_header
            )
        
        response = client.post(
            "/api/transactions/snapshot/generate",
            headers=auth_header
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["balance"]) == 150.0
        assert data["transaction_count"] == 3
    
    def test_verify_snapshot_consistency(self, auth_header):
        """Test snapshot consistency verification"""
        # Add transaction (which auto-generates snapshot)
        client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "credit",
                "idempotency_key": "txn-verify-1"
            },
            headers=auth_header
        )
        
        response = client.get(
            "/api/transactions/snapshot/verify",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_consistent"] == True
        assert float(data["snapshot_balance"]) == float(data["actual_balance"])

class TestAuthentication:
    """Test authentication enforcement"""
    
    def test_transaction_without_auth(self):
        """Test that transactions require authentication"""
        response = client.post(
            "/api/transactions/",
            json={
                "account_id": 1,
                "amount": 100.00,
                "type": "credit",
                "idempotency_key": "txn-noauth"
            }
        )
        assert response.status_code == 403  # Forbidden (no credentials)
    
    def test_balance_without_auth(self):
        """Test that balance endpoint requires authentication"""
        response = client.get("/api/transactions/balance")
        assert response.status_code == 403
    
    def test_invalid_token(self):
        """Test with invalid token"""
        response = client.get(
            "/api/transactions/balance",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
