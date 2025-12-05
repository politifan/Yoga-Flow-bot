import secrets
import time
from typing import Optional, Tuple


class LinkTokenStore:
    """
    In-memory link token storage with TTL.
    For production consider Redis or DB-backed store.
    """

    def __init__(self, ttl_seconds: int = 900):
        self.ttl = ttl_seconds
        self._tokens: dict[str, Tuple[str, float]] = {}

    def create(self, user_id: str) -> tuple[str, float]:
        token = secrets.token_urlsafe(16)
        expires_at = time.time() + self.ttl
        self._tokens[token] = (user_id, expires_at)
        return token, expires_at

    def consume(self, token: str) -> Optional[str]:
        """
        Return user_id and delete token if valid and not expired.
        """
        entry = self._tokens.get(token)
        if not entry:
            return None
        user_id, expires_at = entry
        if expires_at < time.time():
            self._tokens.pop(token, None)
            return None
        self._tokens.pop(token, None)
        return user_id

    def validate(self, token: str) -> Optional[str]:
        """
        Return user_id if valid (without consuming).
        """
        entry = self._tokens.get(token)
        if not entry:
            return None
        user_id, expires_at = entry
        if expires_at < time.time():
            self._tokens.pop(token, None)
            return None
        return user_id
