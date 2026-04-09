from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionHistory
from app.services.transaction_service import (
    create_transaction,
    get_transaction_history,
    get_current_balance
)
from app.services.snapshot_service import (
    get_latest_snapshot,
    generate_snapshot,
    verify_balance_consistency
)
from app.api.deps import get_db, get_current_user, get_current_account_id

router = APIRouter(tags=["transactions"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_txn(
    data: TransactionCreate,
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction (credit or debit).
    
    - **amount**: Must be positive (specify in type: credit/debit)
    - **type**: 'credit' or 'debit'
    - **idempotency_key**: Unique key to prevent duplicate transactions
    """
    # Always use authenticated user's account ID, ignore the one in request body
    return create_transaction(db, current_user.id, data)

@router.get("/balance", response_model=dict)
def get_balance(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current account balance"""
    balance = get_current_balance(db, current_user.id)
    return {
        "account_id": current_user.id,
        "current_balance": float(balance)
    }

@router.get("/history", response_model=dict)
def get_history(
    limit: int = Query(50, gt=0, le=500),
    offset: int = Query(0, ge=0),
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history with pagination.
    
    - **limit**: Number of transactions to return (max 500)
    - **offset**: Number of transactions to skip for pagination
    """
    result = get_transaction_history(db, current_user.id, limit, offset)
    return {
        "transactions": result["transactions"],
        "total_count": result["total_count"],
        "current_balance": float(result["balance"]),
        "limit": limit,
        "offset": offset
    }

@router.get("/snapshot/latest", response_model=dict)
def get_latest_balance_snapshot(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest balance snapshot"""
    snapshot = get_latest_snapshot(db, current_user.id)
    return {
        "snapshot_id": snapshot.id,
        "account_id": snapshot.account_id,
        "balance": float(snapshot.balance),
        "transaction_count": snapshot.transaction_count,
        "created_at": snapshot.created_at
    }

@router.post("/snapshot/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_new_snapshot(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually generate a new balance snapshot for audit purposes"""
    snapshot = generate_snapshot(db, current_user.id)
    return {
        "snapshot_id": snapshot.id,
        "account_id": snapshot.account_id,
        "balance": float(snapshot.balance),
        "transaction_count": snapshot.transaction_count,
        "created_at": snapshot.created_at
    }

@router.get("/snapshot/verify", response_model=dict)
def verify_snapshot_consistency(
    current_user: Account = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify that snapshot balance matches actual transaction sum"""
    result = verify_balance_consistency(db, current_user.id)
    return {
        "account_id": result["account_id"],
        "snapshot_balance": float(result["snapshot_balance"]),
        "actual_balance": float(result["actual_balance"]),
        "is_consistent": result["is_consistent"],
        "last_snapshot_time": result["last_snapshot_time"]
    }
