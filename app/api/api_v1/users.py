
from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.model import User
from app.util import Util

router = APIRouter()

@router.get(
    "/info",name="获取用户详情")
async def test(request: Request):
    user_obj = await User.get_or_none(openid=request.state.openid)

    return Util.format_Resp(data=User.toDict(user_obj))
