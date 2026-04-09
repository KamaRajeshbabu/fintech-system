from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

class TransactionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    account_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: str = Field(..., pattern="^(credit|debit)$")
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()), min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('type')
    @classmethod
    def valid_type(cls, v):
        if v not in ['credit', 'debit']:
            raise ValueError("Type must be 'credit' or 'debit'")
        return v

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    amount: Decimal
    type: str
    idempotency_key: str
    description: Optional[str]
    created_at: datetime

class TransactionHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    transactions: list[TransactionResponse]
    total_count: int
    balance: Decimal
