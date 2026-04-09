from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas.account import AccountCreate, AccountLogin
from app.schemas.auth import TokenResponse
from app.services.auth_service import register_account, authenticate_account
from app.api.deps import get_db

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(data: AccountCreate, db: Session = Depends(get_db)):
    """Register a new account"""
    return register_account(db, data)

@router.post("/login", response_model=TokenResponse)
def login(data: AccountLogin, db: Session = Depends(get_db)):
    """Login to existing account and get access token"""
    result = authenticate_account(db, data)
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "expires_in": 86400  # 24 hours in seconds
    }
