from fastapi import APIRouter
from app.api.v1.endpoints import reservations, guests, rooms, availability, rates
from app.api.v1 import analytics

api_router = APIRouter()

api_router.include_router(
    reservations.router, prefix="/reservations", tags=["reservations"]
)
api_router.include_router(guests.router, prefix="/guests", tags=["guests"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(
    availability.router, prefix="/availability", tags=["availability"]
)
api_router.include_router(rates.router, prefix="/rates", tags=["rates"])
api_router.include_router(analytics.router, prefix="/analytics")
