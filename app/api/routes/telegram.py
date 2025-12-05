from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.dependencies import get_link_token_store
from app.services.link_tokens import LinkTokenStore


class LinkTokenRequest(BaseModel):
    user_id: str


class LinkTokenResponse(BaseModel):
    link_token: str
    telegram_deeplink: str | None
    expires_at: float


router = APIRouter()


@router.post("/link-token", response_model=LinkTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_link_token(
    payload: LinkTokenRequest,
    store: LinkTokenStore = Depends(get_link_token_store),
    settings: Settings = Depends(get_settings),
) -> LinkTokenResponse:
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

    token, expires_at = store.create(payload.user_id)
    deeplink = None
    if settings.bot_username:
        deeplink = f"https://t.me/{settings.bot_username}?start={token}"

    return LinkTokenResponse(link_token=token, telegram_deeplink=deeplink, expires_at=expires_at)
