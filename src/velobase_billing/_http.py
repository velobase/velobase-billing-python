from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import httpx

from ._errors import (
    AuthenticationError,
    ConflictError,
    InternalError,
    NotFoundError,
    ValidationError,
    VelobaseError,
)

T = TypeVar("T")

_STATUS_MAP: Dict[int, Type[VelobaseError]] = {
    400: ValidationError,
    401: AuthenticationError,
    404: NotFoundError,
    409: ConflictError,
    500: InternalError,
}


def _raise_for_status(status: int, message: str, error_type: str) -> None:
    cls = _STATUS_MAP.get(status)
    if cls:
        raise cls(message)
    raise VelobaseError(message, status, error_type)


def _is_retryable(status: int) -> bool:
    return status >= 500 or status == 429


_CAMEL_RE = re.compile(r"([A-Z])")


def _to_snake_case(name: str) -> str:
    return _CAMEL_RE.sub(r"_\1", name).lower()


def _convert_keys(obj: Union[Dict[str, Any], List[Any], Any]) -> Any:
    if isinstance(obj, dict):
        return {_to_snake_case(k): _convert_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_keys(item) for item in obj]
    return obj


class SyncHttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float,
        max_retries: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                delay = min(0.5 * (2 ** (attempt - 1)), 5.0)
                time.sleep(delay)

            try:
                response = self._client.request(
                    method,
                    path,
                    json=body,
                    headers=headers,
                )

                if not response.is_success:
                    try:
                        data = response.json()
                        error = data.get("error", {})
                        msg = error.get("message", f"HTTP {response.status_code}")
                        error_type = error.get("type", "unknown_error")
                    except Exception:
                        msg = f"HTTP {response.status_code}"
                        error_type = "unknown_error"

                    if _is_retryable(response.status_code) and attempt < self._max_retries:
                        last_error = VelobaseError(msg, response.status_code, error_type)
                        continue

                    _raise_for_status(response.status_code, msg, error_type)

                return _convert_keys(response.json())

            except VelobaseError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self._max_retries:
                    continue
                raise VelobaseError(
                    f"Request failed: {exc}", 0, "network_error"
                ) from exc

        raise last_error  # type: ignore[misc]

    def close(self) -> None:
        self._client.close()


class AsyncHttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float,
        max_retries: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        import asyncio

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                delay = min(0.5 * (2 ** (attempt - 1)), 5.0)
                await asyncio.sleep(delay)

            try:
                response = await self._client.request(
                    method,
                    path,
                    json=body,
                    headers=headers,
                )

                if not response.is_success:
                    try:
                        data = response.json()
                        error = data.get("error", {})
                        msg = error.get("message", f"HTTP {response.status_code}")
                        error_type = error.get("type", "unknown_error")
                    except Exception:
                        msg = f"HTTP {response.status_code}"
                        error_type = "unknown_error"

                    if _is_retryable(response.status_code) and attempt < self._max_retries:
                        last_error = VelobaseError(msg, response.status_code, error_type)
                        continue

                    _raise_for_status(response.status_code, msg, error_type)

                return _convert_keys(response.json())

            except VelobaseError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self._max_retries:
                    continue
                raise VelobaseError(
                    f"Request failed: {exc}", 0, "network_error"
                ) from exc

        raise last_error  # type: ignore[misc]

    async def close(self) -> None:
        await self._client.aclose()
