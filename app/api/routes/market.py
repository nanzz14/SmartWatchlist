from fastapi import APIRouter
from app.services.market_data import fetch_market

router = APIRouter(
    prefix="/api/market",
    tags=["market"]
)


@router.post("/analyze")
async def analyze_market(
    payload: dict
):
    symbols = payload.get("symbols", [])

    result = fetch_market(symbols)

    return result