from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, func, Index
from app.core.database import Base

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    balance = Column(Numeric(15, 2), nullable=False)
    transaction_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    __table_args__ = (
        Index('idx_account_snapshot', 'account_id', 'created_at'),
    )