from __future__ import annotations

from typing import Any, Dict, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ConsumeResponse, FreezeResponse, UnfreezeResponse


class BillingResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def freeze(
        self,
        *,
        customer_id: str,
        amount: float,
        business_id: str,
        business_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FreezeResponse:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "business_id": business_id,
        }
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description

        data = self._http.request("POST", "/v1/billing/freeze", body=body)
        return FreezeResponse.model_validate(data)

    def consume(
        self,
        *,
        business_id: str,
        actual_amount: Optional[float] = None,
    ) -> ConsumeResponse:
        body: Dict[str, Any] = {"business_id": business_id}
        if actual_amount is not None:
            body["actual_amount"] = actual_amount

        data = self._http.request("POST", "/v1/billing/consume", body=body)
        return ConsumeResponse.model_validate(data)

    def unfreeze(self, *, business_id: str) -> UnfreezeResponse:
        body = {"business_id": business_id}
        data = self._http.request("POST", "/v1/billing/unfreeze", body=body)
        return UnfreezeResponse.model_validate(data)


class AsyncBillingResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def freeze(
        self,
        *,
        customer_id: str,
        amount: float,
        business_id: str,
        business_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FreezeResponse:
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "amount": amount,
            "business_id": business_id,
        }
        if business_type is not None:
            body["business_type"] = business_type
        if description is not None:
            body["description"] = description

        data = await self._http.request("POST", "/v1/billing/freeze", body=body)
        return FreezeResponse.model_validate(data)

    async def consume(
        self,
        *,
        business_id: str,
        actual_amount: Optional[float] = None,
    ) -> ConsumeResponse:
        body: Dict[str, Any] = {"business_id": business_id}
        if actual_amount is not None:
            body["actual_amount"] = actual_amount

        data = await self._http.request("POST", "/v1/billing/consume", body=body)
        return ConsumeResponse.model_validate(data)

    async def unfreeze(self, *, business_id: str) -> UnfreezeResponse:
        body = {"business_id": business_id}
        data = await self._http.request("POST", "/v1/billing/unfreeze", body=body)
        return UnfreezeResponse.model_validate(data)
