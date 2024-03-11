import asyncio
from uuid import uuid4
from time import time

from tortoise import fields
from tortoise.functions import Count

from app.models import BaseModel
from tortoise.models import Model

from app.util import Util, OSS
from app.mapping import CodeStatus


class User(BaseModel):
    # 用户信息表
    class Meta:
        table = "user"

    username = fields.CharField(40, default="")  # 用户名
    password = fields.CharField(40, default="")  # 密码
    avatar_url = fields.CharField(500, default="")  # 微信头像
    nickname = fields.CharField(40, default="")  # 微信昵称
    wxid = fields.CharField(40, default="", unique=True)  # 微信ID，用于唯一标识用户
    phone = fields.CharField(40, default="")  # 电话
    active = fields.IntField(default=1)  # 表示账号的激活状态，1表示已激活，0表示未激活
    gender = fields.IntField(default=1)  # 性别，0表示男，1表示nv
    openid = fields.CharField(40, default="", unique=True)  # 小程序唯一标识别
    unionid = fields.CharField(40, default="", unique=True)  # unionId: 用于唯一标识用户在不同应用或平台中的身份关联（web 跟小程序的唯一标识）
    country = fields.CharField(40, default="")  # 用户所在国家
    province = fields.CharField(40, default="")  # 用户所在省份
    city = fields.CharField(40, default="")  # 用户所在城市


class Message(BaseModel):
    # 聊天记录
    class Meta:
        table = "message"

    session_id = fields.CharField(50, description="会话id", null=False)
    message = fields.TextField(default=None, description="消息", null=True)
    message_type = fields.IntField(default=1, description="消息类型 1:text 2:audio")
    openid = fields.CharField(30, default=None, description="openid", null=True)
    bot_id = fields.IntField(default=None, description="bot_id", null=True)
    chat_id = fields.CharField(50, description="chat_id", null=False)
    source_url = fields.CharField(200, default=None, description="source_url", null=True)

    @classmethod
    async def get_all(cls, page=None, pageSize=None, filterParams={}, orderBy="id",
                      delKeys=["gmt_modified"]):
        original_result = await super().get_all(page=page, pageSize=pageSize, filterParams=filterParams,
                                                orderBy=orderBy, delKeys=delKeys)
        for item in original_result.get("data", []):
            file_path = item.get("source_url")
            if file_path:
                item["source_url"] = OSS.get_temp_url(file_path)
        return original_result
