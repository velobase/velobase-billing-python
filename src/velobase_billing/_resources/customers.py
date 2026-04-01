from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import CustomerResponse, DepositResponse


class CustomersResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def deposit(
        self,
        *,
        customer_id: str,
        amount: float,
        idempotency_key: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> DepositResponse:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
        }
        if idempotency_key is not None:
            body["idempotency_key"] = idempotency_key
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if metadata is not None:
            body["metadata"] = metadata
        if description is not None:
            body["description"] = description

        headers: Optional[Dict[str, str]] = None
        if idempotency_key is not None:
            headers = {"Idempotency-Key": idempotency_key}

        data = self._http.request(
            "POST", "/v1/customers/deposit", body=body, headers=headers
        )
        return DepositResponse.model_validate(data)

    def get(self, customer_id: str) -> CustomerResponse:
        data = self._http.request(
            "GET", f"/v1/customers/{quote(customer_id, safe='')}"
        )
        return CustomerResponse.model_validate(data)


class AsyncCustomersResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def deposit(
        self,
        *,
        customer_id: str,
        amount: float,
        idempotency_key: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> DepositResponse:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
        }
        if idempotency_key is not None:
            body["idempotency_key"] = idempotency_key
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if metadata is not None:
            body["metadata"] = metadata
        if description is not None:
            body["description"] = description

        headers: Optional[Dict[str, str]] = None
        if idempotency_key is not None:
            headers = {"Idempotency-Key": idempotency_key}

        data = await self._http.request(
            "POST", "/v1/customers/deposit", body=body, headers=headers
        )
        return DepositResponse.model_validate(data)

    async def get(self, customer_id: str) -> CustomerResponse:
        data = await self._http.request(
            "GET", f"/v1/customers/{quote(customer_id, safe='')}"
        )
        return CustomerResponse.model_validate(data)
