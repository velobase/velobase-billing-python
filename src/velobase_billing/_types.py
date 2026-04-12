from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ─── Freeze ───────────────────────────────────────────────────────


class FreezeResponse(BaseModel):
    transaction_id: str
    frozen_amount: float
    freeze_details: List[Any]
    is_idempotent_replay: bool


# ─── Consume ──────────────────────────────────────────────────────


class ConsumeResponse(BaseModel):
    transaction_id: str
    consumed_amount: float
    returned_amount: Optional[float] = None
    consume_details: List[Any]
    consumed_at: str
    is_idempotent_replay: bool


# ─── Unfreeze ─────────────────────────────────────────────────────


class UnfreezeResponse(BaseModel):
    transaction_id: str
    unfrozen_amount: float
    unfreeze_details: List[Any]
    unfrozen_at: str
    is_idempotent_replay: bool


# ─── Deposit ──────────────────────────────────────────────────────


class DepositResponse(BaseModel):
    customer_id: str
    account_id: str
    credit_type: Optional[str] = None
    total_amount: float
    added_amount: float
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    record_id: str
    is_idempotent_replay: bool


# ─── Deduct ───────────────────────────────────────────────────────


class DeductResponse(BaseModel):
    transaction_id: str
    deducted_amount: float
    deduct_details: List[Any]
    deducted_at: str
    is_idempotent_replay: bool


# ─── Customer ─────────────────────────────────────────────────────


class CustomerBalance(BaseModel):
    total: float
    used: float
    frozen: float
    available: float


class CustomerAccount(BaseModel):
    account_type: str
    credit_type: str
    total: float
    used: float
    frozen: float
    available: float
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    balance: CustomerBalance
    accounts: List[CustomerAccount]
    created_at: str


# ─── Ledger ──────────────────────────────────────────────────────


class LedgerEntry(BaseModel):
    id: str
    operation_type: str
    amount: float
    credit_type: str
    transaction_id: Optional[str] = None
    business_type: str
    description: Optional[str] = None
    account_id: str
    status: str
    created_at: str


class LedgerResponse(BaseModel):
    items: List[LedgerEntry]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None
