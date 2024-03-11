from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional

from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash

# from app.utils import (
#     generate_password_reset_token,
#     send_reset_password_email,
#     verify_password_reset_token,
# )
from app.views import MiniProgram

router = APIRouter()


@router.get("/login/auth", name="验证是否需要授权",
            description="前端通过wx.login 发送code，后端验证用户是否需要授权"
                        "如果不需要授，返回状态200 + token，如果需要授权返回401，前端调wx.getUserProfile让用户授权，然后通过/login/access-token 接口，传送iv+ encryptedData",
            responses={
                200: {"description": "验证成功，跳转主页"},
                400: {"description": "一般是code 有问题，例：invalid code、code been used"},

                401: {"description": "需要绑定,前端让用户授权，调/login/access-token接口时需要传nickname+avatar_url,获取token"}})
async def login_auth(code: str):
    return await MiniProgram.login_auth(code)


class LoginAccessTokenBody(BaseModel):
    code: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


@router.post("/login/access-token", name="获取access-token",
             description="前端传code+nickname+avatar_url，获取token"
                         "过期后接口返回401，前端重新调用wx.login 重新登录，并同步客户数据",
             responses={
                 200: {"description": "验证成功，跳转主页"},
                 400: {"description": "一般是code 有问题，例：invalid code、code been used"}})
async def login_access_token(
        body: LoginAccessTokenBody
):
    return await MiniProgram.login_access_token(dict(body))

# @router.post("/login/test-token")
# def test_token(current_user: CurrentUser) -> Any:
#     """
#     Test access token
#     """
#     return current_user


# @router.post("/password-recovery/{email}")
# def recover_password(email: str, session: SessionDep) -> Message:
#     """
#     Password Recovery
#     """
#     user = crud.get_user_by_email(session=session, email=email)
#
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this username does not exist in the system.",
#         )
#     password_reset_token = generate_password_reset_token(email=email)
#     send_reset_password_email(
#         email_to=user.email, email=email, token=password_reset_token
#     )
#     return Message(message="Password recovery email sent")
#
#
# @router.post("/reset-password/")
# def reset_password(session: SessionDep, body: NewPassword) -> Message:
#     """
#     Reset password
#     """
#     email = verify_password_reset_token(token=body.token)
#     if not email:
#         raise HTTPException(status_code=400, detail="Invalid token")
#     user = crud.get_user_by_email(session=session, email=email)
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this username does not exist in the system.",
#         )
#     elif not user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     hashed_password = get_password_hash(password=body.new_password)
#     user.hashed_password = hashed_password
#     session.add(user)
#     session.commit()
#     return Message(message="Password updated successfully")
