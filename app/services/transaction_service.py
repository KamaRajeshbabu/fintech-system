from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from fastapi import HTTPException, status
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import TransactionCreate
from app.services.snapshot_service import generate_snapshot

def get_current_balance(db: Session, account_id: int) -> float:
    """Calculate current balance from all transactions"""
    result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id
    ).scalar()
    
    # If no transactions, start with 0
    if result is None:
        return 0.0
    
    return float(result) if result is not None else 0.0

def apply_transaction(db: Session, account_id: int, amount: Decimal, txn_type: str) -> float:
    """Apply transaction amount to account balance based on type"""
    current_balance = get_current_balance(db, account_id)
    amount_float = float(amount)
    
    if txn_type == "credit":
        new_balance = current_balance + amount_float
    elif txn_type == "debit":
        new_balance = current_balance - amount_float
        # Prevent overdraft
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Current: {current_balance}, Debit: {amount_float}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction type"
        )
    
    return new_balance

def create_transaction(db: Session, account_id: int, data: TransactionCreate) -> dict:
    """Create a new transaction with idempotency check"""
    # Verify account exists and is active
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Check for duplicate idempotency key (idempotency)
    existing_txn = db.query(Transaction).filter_by(
        idempotency_key=data.idempotency_key
    ).first()
    
    if existing_txn:
        # Return existing transaction (idempotent response)
        return {
            "id": existing_txn.id,
            "account_id": existing_txn.account_id,
            "amount": existing_txn.amount,
            "type": existing_txn.type,
            "idempotency_key": existing_txn.idempotency_key,
            "description": existing_txn.description,
            "created_at": existing_txn.created_at,
            "new_balance": get_current_balance(db, account_id),
            "duplicate": True
        }
    
    # Apply transaction logic to verify it's valid
    new_balance = apply_transaction(db, account_id, data.amount, data.type)
    
    # Create and persist transaction
    txn = Transaction(
        account_id=account_id,
        amount=data.amount,
        type=data.type,
        idempotency_key=data.idempotency_key,
        description=data.description
    )
    
    db.add(txn)
    
    # Update account balance
    account.balance = new_balance
    account.updated_at = func.now()
    
    db.commit()
    db.refresh(txn)
    
    # Generate snapshot for audit trail
    generate_snapshot(db, account_id)
    
    return {
        "id": txn.id,
        "account_id": txn.account_id,
        "amount": txn.amount,
        "type": txn.type,
        "idempotency_key": txn.idempotency_key,
        "description": txn.description,
        "created_at": txn.created_at,
        "new_balance": new_balance,
        "duplicate": False
    }

def get_transaction_history(db: Session, account_id: int, limit: int = 50, offset: int = 0) -> dict:
    """Get transaction history for an account"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Get transactions with pagination
    transactions = db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    total_count = db.query(func.count(Transaction.id)).filter(
        Transaction.account_id == account_id
    ).scalar()
    
    balance = get_current_balance(db, account_id)
    
    # Convert transactions to dictionaries for JSON serialization
    transaction_dicts = [
        {
            "id": t.id,
            "account_id": t.account_id,
            "amount": float(t.amount),
            "type": t.type,
            "idempotency_key": t.idempotency_key,
            "description": t.description,
            "created_at": t.created_at
        }
        for t in transactions
    ]
    
    return {
        "transactions": transaction_dicts,
        "total_count": total_count,
        "balance": balance,
        "limit": limit,
        "offset": offset
    }
