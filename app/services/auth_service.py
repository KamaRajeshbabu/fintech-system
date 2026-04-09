from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.account import Account
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.account import AccountCreate, AccountLogin

def register_account(db: Session, data: AccountCreate) -> dict:
    """Register a new account"""
    # Check if account already exists
    existing_account = db.query(Account).filter(Account.email == data.email).first()
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(data.password)
    
    # Create account
    account = Account(
        email=data.email,
        hashed_password=hashed_password
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {
        "id": account.id,
        "email": account.email,
        "balance": account.balance,
        "status": account.status,
        "created_at": account.created_at
    }

def authenticate_account(db: Session, data: AccountLogin) -> dict:
    """Authenticate account and return access token"""
    # Find account by email
    account = db.query(Account).filter(Account.email == data.email).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(data.password, account.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if account.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create and return token
    access_token = create_access_token(data={"sub": account.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "account_id": account.id,
        "email": account.email
    }
