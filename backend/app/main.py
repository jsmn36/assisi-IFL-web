from fastapi import FastAPI
from .config import settings

app = FastAPI(title="Assisi IFL Web API", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/database/info")
def database_info() -> dict[str, str]:
    # Placeholder for database info
    return {"db": "postgres", "status": "connected"}
