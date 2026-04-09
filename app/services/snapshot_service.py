from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from fastapi import HTTPException, status
from app.models.transaction import Transaction
from app.models.snapshot import Snapshot
from app.models.account import Account

def generate_snapshot(db: Session, account_id: int) -> Snapshot:
    """Generate a balance snapshot for an account at current point in time"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Calculate balance from all transactions
    balance = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id
    ).scalar() or Decimal(0)
    
    # Count transactions for audit
    transaction_count = db.query(func.count(Transaction.id)).filter(
        Transaction.account_id == account_id
    ).scalar() or 0
    
    # Create snapshot
    snapshot = Snapshot(
        account_id=account_id,
        balance=balance,
        transaction_count=transaction_count
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return snapshot

def get_latest_snapshot(db: Session, account_id: int) -> Snapshot:
    """Get the latest snapshot for an account"""
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    snapshot = db.query(Snapshot).filter(
        Snapshot.account_id == account_id
    ).order_by(Snapshot.created_at.desc()).first()
    
    if not snapshot:
        # Generate first snapshot if none exists
        return generate_snapshot(db, account_id)
    
    return snapshot

def verify_balance_consistency(db: Session, account_id: int) -> dict:
    """Verify balance consistency between snapshot and actual transactions"""
    # Get latest snapshot
    snapshot = get_latest_snapshot(db, account_id)
    
    # Calculate actual balance from transactions
    actual_balance = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id
    ).scalar() or Decimal(0)
    
    is_consistent = snapshot.balance == actual_balance
    
    return {
        "account_id": account_id,
        "snapshot_balance": snapshot.balance,
        "actual_balance": actual_balance,
        "is_consistent": is_consistent,
        "last_snapshot_time": snapshot.created_at
    }

def reconstruct_balance_at_time(db: Session, account_id: int, timestamp) -> Decimal:
    """Reconstruct balance at a specific point in time using transactions"""
    balance = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.created_at <= timestamp
    ).scalar() or Decimal(0)
    
    return balance
