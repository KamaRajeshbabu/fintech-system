from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime, func, CheckConstraint, Index
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(String(10), nullable=False)  # 'credit' or 'debit'
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    __table_args__ = (
        CheckConstraint("type IN ('credit', 'debit')", name='valid_transaction_type'),
        CheckConstraint("amount > 0", name='positive_amount'),
        Index('idx_account_created', 'account_id', 'created_at'),
    )