from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./thesis_digest.db"
    # Later change to: "postgresql://user:pass@localhost/thesis_digest"

    # Relevance thresholds
    RELEVANT_SCORE_THRESHOLD: float = 0.6
    HIGH_CONFIDENCE_THRESHOLD: float = 0.8

    # Map Yahoo Finance tickers → human-readable names for RSS search
    STOCK_NAME_MAP: Dict[str, str] = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "TCS Tata Consultancy",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "WIPRO.NS": "Wipro",
        "BHARTIARTL.NS": "Bharti Airtel",
        "ITC.NS": "ITC Limited",
        "SBIN.NS": "State Bank of India",
        "LT.NS": "Larsen Toubro",
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google Alphabet",
        "TSLA": "Tesla",
        "AMZN": "Amazon",
    }


settings = Settings()