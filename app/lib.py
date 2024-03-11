import os
import sys
import time
from random import random

import aiohttp

from app.util import Util


class Lib:

    @classmethod
    async def Request(cls, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"},
                      endpoint=None, methods="get", json=None, token=None, data=None, auth=None, detail=True):
        '''

        :param headers:
        :type headers: dict
        :param endpoint:
        :type endpoint: str
        :param methods: get/post/put/delete
        :type methods: str
        :param json:
        :type json: dict
        :return:
        :rtype:
        '''
        from app import app
        if token:
            headers['Authorization'] = token
        async with getattr(app.Session, methods)(url=endpoint, headers=headers, json=json, data=data,
                                                 auth=aiohttp.BasicAuth(*auth) if auth else None) as response:
            sys_obj = sys._getframe()
            info = {}
            if response.content_type == 'application/json':
                content = await response.json()
            elif "image" in response.content_type:
                content = await response.content.read()
            else:
                content = await response.text()
            if detail:
                status = response.status
                info['responseStatus'] = status
                info['requestUrl'] = str(response.url)
                info['requestMethod'] = response.method
                info['content_type'] = response.content_type
                info['response'] = content
                return info
            else:
                return content
