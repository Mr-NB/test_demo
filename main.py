import os

import aiohttp as aiohttp
import uvicorn
import aioredis
import logging, logging.config, os

from app import app
from app.api.api_v1 import api_router
from app.core.config import settings
from app.models import TORTOISE_ORM
from fastapi import Depends, Header
from typing import Optional
from app.core.config import settings


@app.on_event("startup")
async def startup_event():
    from tortoise.contrib.fastapi import register_tortoise
    time_zone = os.getenv("TIMEZONE", "Asia/Shanghai")
    coon = aiohttp.TCPConnector(ssl=False)
    session = aiohttp.ClientSession(connector=coon, trust_env=True)
    app.Session = session
    # redis
    app.redis = aioredis.from_url(settings.REDIS_URI, encoding="utf-8", decode_responses=True)
    app.include_router(api_router, prefix="/api/v1",
                       responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"},
                                  403: {"description": "Forbidden"}, 200: {"description": "Success"}}, )
    # mysql orm
    register_tortoise(
        app, generate_schemas=True, config=TORTOISE_ORM
    )


@app.on_event("shutdown")
async def shutdown_event():
    await app.Session.close()
    # await app.redis.wait_closed()
    await app.redis.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=settings.SERVER_PORT,
                workers=settings.SERVER_WORKERS)
