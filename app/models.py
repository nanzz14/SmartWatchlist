from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    watchlist_items = relationship("WatchlistItem", back_populates="user")

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(String, nullable=False, index=True)   # e.g. "RELIANCE.NS"
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="watchlist_items")
    thesis = relationship("Thesis", back_populates="watchlist_item", uselist=False)

class Thesis(Base):
    __tablename__ = "theses"
    id = Column(Integer, primary_key=True, index=True)
    watchlist_item_id = Column(Integer, ForeignKey("watchlist_items.id"), unique=True)
    tags = Column(JSON, default=list)                       # ["margin_expansion", "earnings"]
    free_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_reviewed_at = Column(DateTime(timezone=True), server_default=func.now())

    watchlist_item = relationship("WatchlistItem", back_populates="thesis")
    relevance_scores = relationship("RelevanceScore", back_populates="thesis")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String, nullable=False, index=True)
    source = Column(String)                                 # "yahoo", "newsapi", "manual"
    type = Column(String, nullable=False, index=True)       # "earnings_beat", "price_move"...
    payload = Column(JSON)                                  # raw data
    magnitude = Column(Float, default=0.0)                  # how big the event is
    timestamp = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    relevance_scores = relationship("RelevanceScore", back_populates="event")

class RelevanceScore(Base):
    __tablename__ = "relevance_scores"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    thesis_id = Column(Integer, ForeignKey("theses.id"), nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)                   # explainability lives here
    seen = Column(Boolean, default=False)

    event = relationship("Event", back_populates="relevance_scores")
    thesis = relationship("Thesis", back_populates="relevance_scores")