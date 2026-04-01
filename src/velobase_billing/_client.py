from __future__ import annotations

from typing import Optional

from ._http import AsyncHttpClient, SyncHttpClient
from ._resources import (
    AsyncBillingResource,
    AsyncCustomersResource,
    BillingResource,
    CustomersResource,
)

DEFAULT_BASE_URL = "https://api.velobase.io"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class Velobase:
    """Synchronous Velobase Billing client."""

    billing: BillingResource
    customers: CustomersResource

    def __init__(
        self,
        *,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "api_key is required. Get your API key at https://velobase.io"
            )

        http = SyncHttpClient(
            base_url=base_url or DEFAULT_BASE_URL,
            api_key=api_key,
            timeout=timeout or DEFAULT_TIMEOUT,
            max_retries=max_retries if max_retries is not None else DEFAULT_MAX_RETRIES,
        )

        self.billing = BillingResource(http)
        self.customers = CustomersResource(http)
        self._http = http

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Velobase:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncVelobase:
    """Asynchronous Velobase Billing client."""

    billing: AsyncBillingResource
    customers: AsyncCustomersResource

    def __init__(
        self,
        *,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "api_key is required. Get your API key at https://velobase.io"
            )

        http = AsyncHttpClient(
            base_url=base_url or DEFAULT_BASE_URL,
            api_key=api_key,
            timeout=timeout or DEFAULT_TIMEOUT,
            max_retries=max_retries if max_retries is not None else DEFAULT_MAX_RETRIES,
        )

        self.billing = AsyncBillingResource(http)
        self.customers = AsyncCustomersResource(http)
        self._http = http

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> AsyncVelobase:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
