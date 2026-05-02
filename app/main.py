from fastapi import FastAPI
import uvicorn

from app.db.connections import engine
from app.db.base import Base


app = FastAPI(
    title="Auth",
    description="Authorization",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "Auth is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)