from fastapi import APIRouter

from app.api.routes import payments, receipts, subscriptions, telegram

# Main API router; versioned routes will be attached here.
api_router = APIRouter(prefix="/v1")

api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(receipts.router, tags=["receipts"])
