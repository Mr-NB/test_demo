import asyncio
import os
from datetime import datetime, timezone
from enum import Enum
import pytz

import aiomysql
from tortoise.functions import Count
from tortoise.models import Model
from tortoise import fields

from app.util import Util
from app.core.config import settings

TORTOISE_ORM = {
    'connections': {
        'default': settings.MYSQL_URI
    },
    'apps': {
        "models": {'models': ['app.models.model', 'aerich.models'],
                   'default_connection': 'default'}

    },
    'use_tz': False,
    'timezone': settings.TIME_ZONE
}


class BaseModel(Model):
    id = fields.IntField(pk=True)
    gmt_create = fields.DatetimeField(auto_now_add=True)
    gmt_modified = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.id

    @classmethod
    def toDict(cls, obj, delKeys=["gmt_modified", "gmt_create"]):
        if not obj:
            return {}
        data = {}
        for item in obj._meta.fields:
            if item in delKeys:
                continue
            value = getattr(obj, item)
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, datetime):
                value = Util.datetime_to_str(value, "%Y-%m-%d %H:%M:%S")
            else:
                value = getattr(obj, item)
            data[item] = value
        return data

    @classmethod
    async def add(cls, data):
        await cls(**data).save()
        return Util.format_Resp(message="添加成功")

    @classmethod
    async def add_all(cls, data):
        tasks = [cls.add(item) for item in data]
        await asyncio.gather(*tasks)
        return Util.format_Resp(message="添加成功")

    @classmethod
    async def get_one(cls, filterParams=None, delKeys=[]):
        if filterParams:
            queryObj = await cls.get_or_none(**filterParams)
            if not queryObj:
                data = {}
            else:
                data = cls.toDict(queryObj, delKeys=delKeys)
        else:
            data = cls.toDict(await cls.first(), delKeys=delKeys)
        return Util.format_Resp(data=data)

    @classmethod
    async def get_all(cls, page=None, pageSize=None, filterParams={}, orderBy="id",
                      delKeys=["gmt_modified", "gmt_create"]):
        filterObj = cls.filter(**filterParams)
        if page and pageSize:
            data = list(
                map(lambda x: cls.toDict(x, delKeys=delKeys),
                    (await filterObj.offset((int(page) - 1) * int(pageSize)).limit(int(pageSize)).order_by(orderBy))))
            return Util.format_Resp(data=data, count=await filterObj.count(), curPage=page)
        else:
            data = [cls.toDict(item, delKeys=delKeys) for item in await filterObj.all().order_by(orderBy)]
            return Util.format_Resp(data=data)

    @classmethod
    async def remove(cls, id):
        await cls.filter(id=id).delete()
        return Util.format_Resp(message="删除成功")

    @classmethod
    async def update(cls, data):
        '''
        更新，如果没有传id则为新增
        :param data:
        :return:
        '''
        id = data.get("id")
        if not id:
            return await cls.add(data)
        del data["id"]
        data = Util.filter_null(data)
        await cls.filter(id=id).update(**data)
        return Util.format_Resp(message="更新成功", data=data)

    @classmethod
    async def group_by(cls, groupByKey, showKeys=[]):
        # 当对有外键的表进行分组时，显示的id 是groupByKey 的下一个元素的值(注意)
        returnList = await cls.annotate(count=Count("id")).group_by(groupByKey).values(*showKeys, "count", "id",
                                                                                       groupByKey)
        # 关联字段是会有None 的情况[{'root__name': None, 'id': 1, 'count': 1}, {'root__name': '天窗', 'id': 2, 'count': 2}]
        # if "__" in groupByKey:
        # for index in range(len(returnList) - 1, -1, -1):
        #     if not returnList[index].get(groupByKey):
        #         returnList.pop(index)
        return returnList
