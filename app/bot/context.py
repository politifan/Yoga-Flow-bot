from dataclasses import dataclass

import httpx

from app.config import Settings
from app.core_client import CoreAPIClient
from app.services.link_tokens import LinkTokenStore


@dataclass
class BotContext:
    settings: Settings
    core: CoreAPIClient
    integration_client: httpx.AsyncClient
    link_tokens: LinkTokenStore
