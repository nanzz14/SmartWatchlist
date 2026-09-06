from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class ThesisCreate(BaseModel):
    stock_id: str
    tags: List[str] = []
    free_text: Optional[str] = None

class ThesisOut(BaseModel):
    id: int
    stock_id: str
    tags: List[str]
    free_text: Optional[str]
    last_reviewed_at: datetime

    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    stock_id: str
    source: str = "manual"
    type: str
    payload: dict = {}
    magnitude: float = 0.0
    timestamp: datetime

class RelevanceOut(BaseModel):
    event_id: int
    score: float
    confidence: float
    reason: str
    event_type: str
    event_timestamp: datetime
    payload: dict

class DigestOut(BaseModel):
    stock_id: str
    materially_relevant: List[RelevanceOut]
    changed_but_not_relevant: List[RelevanceOut]
    quiet: bool
    last_reviewed_at: datetime