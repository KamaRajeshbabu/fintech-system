from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class AccountCreate(BaseModel):
    email: EmailStr
    password: str

class AccountLogin(BaseModel):
    email: EmailStr
    password: str

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    balance: float
    status: str
    created_at: datetime

class AccountDetail(AccountResponse):
    updated_at: datetime
