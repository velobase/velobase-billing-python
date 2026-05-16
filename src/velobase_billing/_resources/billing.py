from __future__ import annotations

import warnings
from typing import Any, Dict, List, Literal, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ConsumeResponse, DeductResponse, FreezeResponse, UnfreezeResponse


# Single-shot warning dedupe per process. We never want to spam stderr when
# freeze() is called in a hot loop without a TTL field.
_auto_settlement_warning_emitted = False


def _emit_auto_settlement_warning() -> None:
    global _auto_settlement_warning_emitted
    if _auto_settlement_warning_emitted:
        return
    _auto_settlement_warning_emitted = True
    warnings.warn(
        "freeze() called without unfreeze_after_seconds or consume_after_seconds. "
        "This freeze will never auto-settle. Future major versions may require "
        "an explicit choice.",
        DeprecationWarning,
        stacklevel=3,
    )


def _check_auto_settlement_args(
    unfreeze_after_seconds: Optional[int],
    consume_after_seconds: Optional[int],
) -> None:
    if unfreeze_after_seconds is not None and consume_after_seconds is not None:
        raise ValueError(
            "freeze() accepts at most one of unfreeze_after_seconds / "
            "consume_after_seconds, not both"
        )
    if unfreeze_after_seconds is None and consume_after_seconds is None:
        _emit_auto_settlement_warning()

BusinessType = Literal[
    "UNDEFINED",
    "TASK",
    "ORDER",
    "MEMBERSHIP",
    "SUBSCRIPTION",
    "FREE_TRIAL",
    "ADMIN_GRANT",
]

_VALID_BUSINESS_TYPES = frozenset(
    {"UNDEFINED", "TASK", "ORDER", "MEMBERSHIP", "SUBSCRIPTION", "FREE_TRIAL", "ADMIN_GRANT"}
)


def _validate_business_type(value: str) -> None:
    if value not in _VALID_BUSINESS_TYPES:
        valid = ", ".join(sorted(_VALID_BUSINESS_TYPES))
        raise ValueError(
            f"Invalid business_type: {value!r}. Must be one of: {valid}."
        )


class BillingResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def freeze(
        self,
        *,
        customer_id: str,
        amount: float,
        transaction_id: str,
        credit_types: Optional[List[str]] = None,
        business_type: Optional[BusinessType] = None,
        description: Optional[str] = None,
        unfreeze_after_seconds: Optional[int] = None,
        consume_after_seconds: Optional[int] = None,
    ) -> FreezeResponse:
        if business_type is not None:
            _validate_business_type(business_type)
        _check_auto_settlement_args(unfreeze_after_seconds, consume_after_seconds)

        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "transaction_id": transaction_id,
        }
        if credit_types is not None:
            body["credit_types"] = credit_types
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description
        if unfreeze_after_seconds is not None:
            body["unfreeze_after_seconds"] = unfreeze_after_seconds
        if consume_after_seconds is not None:
            body["consume_after_seconds"] = consume_after_seconds

        data = self._http.request("POST", "/v1/billing/freeze", body=body)
        return FreezeResponse.model_validate(data)

    def consume(
        self,
        *,
        transaction_id: str,
        actual_amount: Optional[float] = None,
    ) -> ConsumeResponse:
        body: Dict[str, Any] = {"transaction_id": transaction_id}
        if actual_amount is not None:
            body["actual_amount"] = actual_amount

        data = self._http.request("POST", "/v1/billing/consume", body=body)
        return ConsumeResponse.model_validate(data)

    def unfreeze(self, *, transaction_id: str) -> UnfreezeResponse:
        body = {"transaction_id": transaction_id}
        data = self._http.request("POST", "/v1/billing/unfreeze", body=body)
        return UnfreezeResponse.model_validate(data)

    def deduct(
        self,
        *,
        customer_id: str,
        amount: float,
        transaction_id: str,
        credit_types: Optional[List[str]] = None,
        business_type: Optional[BusinessType] = None,
        description: Optional[str] = None,
    ) -> DeductResponse:
        if business_type is not None:
            _validate_business_type(business_type)

        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "transaction_id": transaction_id,
        }
        if credit_types is not None:
            body["credit_types"] = credit_types
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description

        data = self._http.request("POST", "/v1/billing/deduct", body=body)
        return DeductResponse.model_validate(data)


class AsyncBillingResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def freeze(
        self,
        *,
        customer_id: str,
        amount: float,
        transaction_id: str,
        credit_types: Optional[List[str]] = None,
        business_type: Optional[BusinessType] = None,
        description: Optional[str] = None,
        unfreeze_after_seconds: Optional[int] = None,
        consume_after_seconds: Optional[int] = None,
    ) -> FreezeResponse:
        if business_type is not None:
            _validate_business_type(business_type)
        _check_auto_settlement_args(unfreeze_after_seconds, consume_after_seconds)

        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "transaction_id": transaction_id,
        }
        if credit_types is not None:
            body["credit_types"] = credit_types
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description
        if unfreeze_after_seconds is not None:
            body["unfreeze_after_seconds"] = unfreeze_after_seconds
        if consume_after_seconds is not None:
            body["consume_after_seconds"] = consume_after_seconds

        data = await self._http.request("POST", "/v1/billing/freeze", body=body)
        return FreezeResponse.model_validate(data)

    async def consume(
        self,
        *,
        transaction_id: str,
        actual_amount: Optional[float] = None,
    ) -> ConsumeResponse:
        body: Dict[str, Any] = {"transaction_id": transaction_id}
        if actual_amount is not None:
            body["actual_amount"] = actual_amount

        data = await self._http.request("POST", "/v1/billing/consume", body=body)
        return ConsumeResponse.model_validate(data)

    async def unfreeze(self, *, transaction_id: str) -> UnfreezeResponse:
        body = {"transaction_id": transaction_id}
        data = await self._http.request("POST", "/v1/billing/unfreeze", body=body)
        return UnfreezeResponse.model_validate(data)

    async def deduct(
        self,
        *,
        customer_id: str,
        amount: float,
        transaction_id: str,
        credit_types: Optional[List[str]] = None,
        business_type: Optional[BusinessType] = None,
        description: Optional[str] = None,
    ) -> DeductResponse:
        if business_type is not None:
            _validate_business_type(business_type)

        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "transaction_id": transaction_id,
        }
        if credit_types is not None:
            body["credit_types"] = credit_types
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description

        data = await self._http.request("POST", "/v1/billing/deduct", body=body)
        return DeductResponse.model_validate(data)
