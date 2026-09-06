from fastapi import FastAPI
from app.database import engine, Base
from app.api.routes import thesis, events, digest, ingestion

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Thesis Digest", version="0.1.0")

app.include_router(thesis.router)
app.include_router(events.router)
app.include_router(digest.router)
app.include_router(ingestion.router)

@app.get("/")
def root():
    return {"message": "Thesis Digest API is running"}