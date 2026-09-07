from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import market

app = FastAPI(title="Smart Watchlist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router)


@app.get("/health")
def health():
    return {"message": "Smart Watchlist API is running"}


@app.get("/")
def home():
    return {"message": "Smart Watchlist API is running"}
