# Fintech Backend System

Production-grade financial transaction system with snapshot-based balance engine, idempotency handling, and strong data integrity guarantees.

## 🚀 Live Demo

**Public URL:** https://fintech-system-so25.onrender.com/

## 🏗️ Architecture Overview

This system implements a **ledger-based transaction model** with **snapshot-based balance optimization**:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Auth API   │  │ Transaction  │  │   Snapshot   │       │
│  │  (Register   │  │   Endpoints  │  │  Endpoints   │       │
│  │   & Login)   │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────────────────────────────────────────┬─┘
                                                             │
┌────────────────────────────────────────────────────────────┴─┐
│                  Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Auth Service │  │ Transaction  │  │  Snapshot    │       │
│  │              │  │  Service     │  │  Service     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  • Password Hash   • Idempotency     • Balance Calc         │
│  • Token Gen       • Validation      • Consistency Check    │
└────────────────────────────────────────────────────────────┬─┘
                                                             │
┌────────────────────────────────────────────────────────────┴─┐
│                  Data Layer (SQLAlchemy ORM)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Accounts   │  │ Transactions │  │  Snapshots   │       │
│  │              │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  • Balance      │ • Type (C/D)    │ • Point-in-time        │
│  • Status       │ • Idempotency   │ • Audit Trail          │
└────────────────────────────────────────────────────────────┬─┘
                                                             │
                      SQLite Database
```

### Key Design Decisions

1. **Snapshot-Based Balance Engine**: Periodic snapshots with ledger as source of truth
   - Fast balance lookups
   - Audit trail of all balance states
   - Ability to reconstruct balance at any point in time

2. **Idempotency at Application Level**: `idempotency_key` prevents duplicate transactions
   - Unique constraint on idempotency_key
   - Duplicate requests return the same transaction
   - Safe for retries without risk of double-charging

3. **Credit/Debit Model**: Normalized transaction representation
   - All amounts stored as positive values
   - Type determines direction

4. **Foreign Key Constraints**: Maintain referential integrity with cascading deletes

5. **Indexes for Performance**: Optimized queries for common access patterns

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/KamaRajeshbabu/fintech-system.git
cd fintech-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

Open your browser and go to: `http://localhost:8000`

## 📚 API Documentation

### Base URL
`https://fintech-system.onrender.com`

### Authentication Endpoints

#### 1. Register Account
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Transaction Endpoints

#### 1. Create Transaction
```http
POST /api/transactions/
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100.00,
  "type": "credit",
  "idempotency_key": "txn-001",
  "description": "Salary deposit"
}
```

#### 2. Get Balance
```http
GET /api/transactions/balance
Authorization: Bearer <token>
```

#### 3. Get Transaction History
```http
GET /api/transactions/history
Authorization: Bearer <token>
```

## 🌐 Deployment

### Render.com (Recommended - Free)

1. **Fork this repository** on GitHub
2. **Sign up for Render.com** at https://render.com
3. **Connect your GitHub account**
4. **Create a new Web Service**:
   - Select your forked repository
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. **Add Environment Variables**:
   - `DATABASE_URL`: `sqlite:///./fintech.db`
   - `SECRET_KEY`: Generate a secure random key
6. **Deploy!** Your app will be live at `https://your-app-name.onrender.com`

### Other Deployment Options

#### Railway
```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

#### Heroku
```bash
heroku create your-app-name
git push heroku main
```

## 🧪 Testing

```bash
# Run all tests
pytest app/tests/ -v

# Run specific test file
pytest app/tests/test_auth.py -v
pytest app/tests/test_transactions.py -v
```

## 📁 Project Structure

```
fintech-system/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & CORS setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings & environment
│   │   ├── database.py      # SQLAlchemy setup
│   │   └── security.py      # JWT & password hashing
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py       # User account model
│   │   ├── transaction.py   # Transaction model
│   │   └── snapshot.py      # Balance snapshot model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── account.py       # Pydantic schemas
│   │   ├── auth.py
│   │   └── transaction.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Auth business logic
│   │   ├── transaction_service.py # Transaction logic
│   │   └── snapshot_service.py   # Snapshot logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependencies (auth, db)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py      # Auth endpoints
│   │       └── transactions.py # Transaction endpoints
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py     # Auth tests
│       └── test_transactions.py # Transaction tests
├── frontend.html           # Single-page dashboard
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku/Railway deployment
├── render.yaml           # Render.com deployment
├── pytest.ini           # Test configuration
└── README.md            # This file
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt with passlib
- **Idempotency Keys**: Prevent duplicate transactions
- **Input Validation**: Pydantic schemas
- **CORS Protection**: Configured for frontend access

## 📊 Features

- ✅ **User Registration & Login**
- ✅ **Transaction Creation** (Credit/Debit)
- ✅ **Balance Tracking**
- ✅ **Transaction History**
- ✅ **Snapshot Generation**
- ✅ **Idempotency Handling**
- ✅ **Data Integrity Checks**
- ✅ **Responsive Web Dashboard**
- ✅ **Interactive Charts**
- ✅ **Real-time Updates**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or issues, please open a GitHub issue or contact the maintainers.
}
```

#### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: {"access_token": "...", "token_type": "bearer", "expires_in": 86400}
```

### Transaction Endpoints (Require Authorization Header)

**Authorization: Bearer <access_token>**

#### 3. Create Transaction
```http
POST /api/transactions/

{
  "account_id": 1,
  "amount": 150.50,
  "type": "credit",
  "idempotency_key": "salary-2024-01-01-uuid",
  "description": "Monthly salary"
}
```

**Types**: `credit` (add funds), `debit` (withdraw funds)

#### 4. Get Balance
```http
GET /api/transactions/balance
```

#### 5. Get Transaction History
```http
GET /api/transactions/history?limit=50&offset=0
```

#### 6. Get Latest Snapshot
```http
GET /api/transactions/snapshot/latest
```

#### 7. Generate Snapshot
```http
POST /api/transactions/snapshot/generate
```

#### 8. Verify Consistency
```http
GET /api/transactions/snapshot/verify
```

## 🧪 Testing

```bash
# Run all tests
pytest app/tests/ -v

# Run specific test file
pytest app/tests/test_transactions.py -v

# Run specific test
pytest app/tests/test_transactions.py::TestIdempotency::test_duplicate_transaction_idempotent -v
```

### Test Coverage
- ✅ Authentication (registration, login, password verification)
- ✅ Transaction creation with validation
- ✅ Idempotency handling
- ✅ Balance calculations
- ✅ Overdraft prevention
- ✅ Transaction history with pagination
- ✅ Snapshot generation and consistency
- ✅ Concurrent transaction safety

## 📦 Data Models

### Account
```python
{
  "id": int,
  "email": str,
  "hashed_password": str,
  "balance": Decimal(15, 2),
  "status": str,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Transaction
```python
{
  "id": int,
  "account_id": int,
  "amount": Decimal(15, 2),  # Always positive
  "type": str,               # "credit" or "debit"
  "idempotency_key": str,    # Unique
  "description": str,
  "created_at": datetime
}
```

### Snapshot
```python
{
  "id": int,
  "account_id": int,
  "balance": Decimal(15, 2),
  "transaction_count": int,
  "created_at": datetime
}
```

## 🔒 Security Features

1. **Password Hashing**: Bcrypt with salt
2. **JWT Authentication**: HS256, 24-hour expiration
3. **Input Validation**: Pydantic models with type checking
4. **SQL Injection Prevention**: SQLAlchemy ORM
5. **Idempotency**: Prevents duplicate charges
6. **Database Constraints**: Enforced at DB level

## 📊 Database Schema (Automatic)

Tables are automatically created on app startup via SQLAlchemy ORM:
- `accounts` - User accounts with balance
- `transactions` - Complete audit trail
- `snapshots` - Point-in-time balance states

Indexes created for:
- Account lookups by email
- Transaction history by account+date
- Idempotency key checks

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Reset database
docker-compose down -v
```

## Example Workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"secure123"}'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"secure123"}' \
  | jq -r .access_token)

# 3. Deposit
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 500.00,
    "type": "credit",
    "idempotency_key": "deposit-001"
  }'

# 4. Check balance
curl -X GET http://localhost:8000/api/transactions/balance \
  -H "Authorization: Bearer $TOKEN"

# 5. Withdraw
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 100.00,
    "type": "debit",
    "idempotency_key": "withdrawal-001"
  }'

# 6. View history
curl -X GET "http://localhost:8000/api/transactions/history?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

## 🚨 Error Handling

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | |
| 201 | Created | |
| 400 | Bad Request | Insufficient balance, invalid amount |
| 401 | Unauthorized | Invalid token, missing credentials |
| 403 | Forbidden | Inactive account |
| 404 | Not Found | Account not found |
| 422 | Validation Error | Invalid email, missing field |

## Production Deployment

1. Update environment variables in `.env`
   ```
   SECRET_KEY=<long-random-key>
   DATABASE_URL=<production-db>
   DEBUG=False
   ```

2. Use managed database (AWS RDS, Azure, etc.)

3. Deploy behind reverse proxy with SSL/TLS

4. Add rate limiting and monitoring

5. Enable automated backups

6. Set up CI/CD pipeline

## License

MIT License - See LICENSE file for details
