from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from .config import settings
from .database import get_db

app = FastAPI(title="Assisi IFL Web API", version="0.1.0")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "Assisi IFL API is running"}

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "env": settings.APP_ENV}

@app.get("/database/info")
def database_info(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        # Run a simple query to ensure the database is connected
        db.execute(text("SELECT 1"))
        return {"db": "postgres", "status": "connected"}
    except Exception as e:
        return {"db": "postgres", "status": f"disconnected - {str(e)}"}
