from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints import router

app = FastAPI(
    title="Music Assistant Backend V3 API",
    description="Asynchronous audio analysis API with Celery task processing",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Music Assistant Backend V3 API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}