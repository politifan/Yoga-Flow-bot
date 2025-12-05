from typing import Any, Dict, Optional

import httpx

from app.config import Settings


class CoreAPIClient:
    """
    Thin HTTP client for Core API.
    Assumes Core API returns JSON and uses bearer service token auth.
    """

    def __init__(self, settings: Settings):
        self.base_url = settings.core_api_base_url.rstrip("/")
        headers = {"Authorization": f"Bearer {settings.service_token}"}
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=10.0)

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._client.post(path, json=payload)
        response.raise_for_status()
        return response.json()

    async def patch(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._client.patch(path, json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "CoreAPIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
