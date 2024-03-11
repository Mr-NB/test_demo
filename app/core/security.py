from datetime import datetime, timedelta
from typing import Any, Union

from jose import jwt, ExpiredSignatureError
from jose.exceptions import JWSSignatureError
from passlib.context import CryptContext

from app.core.config import settings
from app.util import Util
from app.mapping import CodeStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    '''
    生成token
    '''
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode = {"exp": expire, "sub": str(subject)}
    else:
        to_encode = {"sub": str(subject)}
    # to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 验证token
def verify_token(token):
    try:

        if "Bearer" in token:
            token = token.replace("Bearer ", "")
        # 解码JWT token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        return Util.format_Resp(data=decoded)
    except ExpiredSignatureError:
        # token过期
        return Util.format_Resp(code_type=CodeStatus.Unauthorized, message='Token expired')
    except JWSSignatureError:
        return Util.format_Resp(code_type=CodeStatus.Unauthorized, message='InValid Token')
