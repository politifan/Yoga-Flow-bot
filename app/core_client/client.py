import asyncio
import logging
from typing import Any, Dict, Iterable, Optional

import httpx

from app.config import Settings
from app.core_client.schemas import (
    Call,
    Course,
    CreateSubscriptionRequest,
    CreateTransactionRequest,
    PatchTransactionRequest,
    Subscription,
    Tariff,
    Transaction,
    User,
)

logger = logging.getLogger(__name__)


class CoreAPIError(Exception):
    def __init__(self, status_code: int, code: Optional[str], message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.details = details


class CoreAPIClient:
    """
    Thin HTTP client for Core API.
    Assumes Core API returns JSON and uses bearer service token auth.
    """

    def __init__(self, settings: Settings):
        self.base_url = settings.core_api_base_url.rstrip("/")
        headers = {"Authorization": f"Bearer {settings.service_token}"}
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10.0)
        self.retries = settings.http_max_retries
        self.backoff = settings.http_retry_backoff

    async def _handle_response(self, response: httpx.Response, allow_statuses: Optional[Iterable[int]] = None) -> Any:
        if allow_statuses and response.status_code in allow_statuses:
            return None
        if response.status_code >= 400:
            code = None
            message = response.text
            details = None
            try:
                payload = response.json()
                code = payload.get("code")
                message = payload.get("message", message)
                details = payload.get("details")
            except Exception:
                pass
            raise CoreAPIError(response.status_code, code, message, details)
        return response.json()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        allow_statuses: Optional[Iterable[int]] = None,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = await self._client.request(method, path, params=params, json=json)
                if response.status_code >= 500 and attempt < self.retries:
                    logger.warning(
                        "Core API %s %s -> %s, retrying (%s/%s)",
                        method,
                        path,
                        response.status_code,
                        attempt + 1,
                        self.retries,
                    )
                    await asyncio.sleep(self.backoff * (attempt + 1))
                    continue
                return await self._handle_response(response, allow_statuses=allow_statuses)
            except httpx.RequestError as err:
                last_error = err
                if attempt >= self.retries:
                    break
                logger.warning(
                    "Core API request error %s %s: %s (retry %s/%s)",
                    method,
                    path,
                    err,
                    attempt + 1,
                    self.retries,
                )
                await asyncio.sleep(self.backoff * (attempt + 1))
        if last_error:
            raise last_error
        raise CoreAPIError(500, "unknown_error", "Request failed", None)

    async def get_user(self, user_id: str) -> User:
        data = await self._request("GET", f"/core/users/{user_id}")
        return User.model_validate(data)

    async def get_user_by_telegram(self, telegram_user_id: int) -> Optional[User]:
        data = await self._request(
            "GET", f"/core/users/by_telegram/{telegram_user_id}", allow_statuses=[404]
        )
        return User.model_validate(data) if data else None

    async def link_telegram(self, user_id: str, telegram_user_id: int, link_token: str) -> dict[str, Any]:
        payload = {"telegram_user_id": telegram_user_id, "link_token": link_token}
        data = await self._request("POST", f"/core/users/{user_id}/telegram/link", json=payload)
        return data if isinstance(data, dict) else {}

    async def get_tariffs(self) -> list[Tariff]:
        data = await self._request("GET", "/core/tariffs")
        return [Tariff.model_validate(item) for item in data]

    async def create_transaction(self, req: CreateTransactionRequest) -> Transaction:
        data = await self._request("POST", "/core/transactions", json=req.model_dump())
        return Transaction.model_validate(data)

    async def patch_transaction(self, transaction_id: str, req: PatchTransactionRequest) -> Transaction:
        data = await self._request("PATCH", f"/core/transactions/{transaction_id}", json=req.model_dump())
        return Transaction.model_validate(data)

    async def get_subscription_by_user(self, user_id: str) -> Optional[Subscription]:
        data = await self._request("GET", f"/core/subscriptions/by_user/{user_id}", allow_statuses=[404])
        return Subscription.model_validate(data) if data else None

    async def create_subscription(self, req: CreateSubscriptionRequest) -> Subscription:
        data = await self._request("POST", "/core/subscriptions", json=req.model_dump())
        return Subscription.model_validate(data)

    async def get_transaction_by_provider_id(self, provider_payment_id: str) -> Optional[Transaction]:
        data = await self._request(
            "GET",
            f"/core/transactions/by_provider_id/{provider_payment_id}",
            allow_statuses=[404],
        )
        return Transaction.model_validate(data) if data else None

    async def get_available_courses(self, user_id: str) -> list[Course]:
        data = await self._request("GET", "/core/courses/available", params={"user_id": user_id})
        return [Course.model_validate(item) for item in data]

    async def get_upcoming_calls(self, user_id: str) -> list[Call]:
        data = await self._request("GET", "/core/calls/upcoming", params={"user_id": user_id})
        return [Call.model_validate(item) for item in data]

    async def get_transaction(self, transaction_id: str) -> Transaction:
        data = await self._request("GET", f"/core/transactions/{transaction_id}")
        return Transaction.model_validate(data)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "CoreAPIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
