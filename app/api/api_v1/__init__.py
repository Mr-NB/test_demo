from fastapi import APIRouter
from typing import Optional
from fastapi import Header, Depends
from app.core.config import settings

from app.api.api_v1 import login, users, utils, chat


async def get_token_header(token: str = Header(settings.TEST_TOKEN)):
    # if not token:
    #     raise HTTPException(status_code=401, detail="No Authorization")
    return


api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"], dependencies=[Depends(get_token_header)])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"], dependencies=[Depends(get_token_header)])
