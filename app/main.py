from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.scheduler.jobs import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Wasaya API",
    version="1.0.0",
    lifespan=lifespan,
)


"""
Enable CORS for the frontend dev server. Keep this list focused and simple for the MVP.
"""
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Global exception handler — keeps errors in {message: ...} format
# ------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred"},
    )


app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}