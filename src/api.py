from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from business.chat import router as chat_router
from business.groups import router as groups_router
from business.user import router as user_router
from business.friends import router as friends_router
from core.config import CONFIG
from core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Phishers Marketplace API", version="1.0.0", default_response_class=ORJSONResponse, lifespan=lifespan
)

app.include_router(user_router)
app.include_router(chat_router)
app.include_router(groups_router)
app.include_router(friends_router)

origins = ["http://localhost", "http://localhost:3000", "http://localhost:9000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Phishers Marketplace!"}


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=CONFIG.UVICORN.HOST,
        port=CONFIG.UVICORN.PORT,
        workers=CONFIG.UVICORN.WORKERS,
        reload=CONFIG.UVICORN.RELOAD_ON_CHANGE,
    )
