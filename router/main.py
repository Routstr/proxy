import asyncio
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .admin import admin_router
from .proxy import proxy_router
from .account import wallet_router
from .models import MODELS, update_sats_pricing
from .cashu import check_for_refunds, init_wallet, close_wallet
from .discovery import providers_router

__version__ = "0.0.1"

@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await init_wallet()
    asyncio.create_task(update_sats_pricing())
    asyncio.create_task(check_for_refunds())
    
    yield
    
    await close_wallet()


app = FastAPI(
    version=__version__,
    title=os.environ.get("NAME", "ARoutstrNode" + __version__),
    description=os.environ.get("DESCRIPTION", "A Routstr Node"),
    contact={"name": os.environ.get("NAME", ""), "npub": os.environ.get("NPUB", "")},
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def info():
    return {
        "name": app.title,
        "description": app.description,
        "version": __version__,
        "npub": os.environ.get("NPUB", ""),
        "mint": os.environ.get("MINT", ""),
        "http_url": os.environ.get("HTTP_URL", ""),
        "onion_url": os.environ.get("ONION_URL", ""),
        "models": MODELS,
    }


app.include_router(admin_router)
app.include_router(wallet_router)
app.include_router(providers_router)
app.include_router(proxy_router)
