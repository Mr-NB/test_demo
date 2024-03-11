import sys, re, logging, hashlib, json
from datetime import datetime
from time import time
from random import random
import os

from app.core.config import settings

import asyncoss
import oss2

from app.mapping import *


class Util:
    @classmethod
    def format_Resp(cls, code_type=CodeStatus.SuccessCode,
                    data='',
                    message='',
                    sys_obj=None,
                    exp_obj=None,
                    exception='',
                    **kwargs
                    ):
        '''
        定义返回Response模板
        :param code_type:   int|错误状态
        :param errorDetail: str|错误详情
        :param data:   str|request成功后填充
        :param message:  str|提示信息
        :param sys_obj:  Obj|获取当前文件名,函数名,所在行数
        :return:
        '''
        Resp = {}
        Resp['code'] = code_type.value

        if sys_obj:
            Resp['errorDetail'] = {"file": sys_obj.f_code.co_filename.split('/')[-1],
                                   "function": sys_obj.f_code.co_name,
                                   "lineNo": sys_obj.f_lineno,
                                   "exception": exception
                                   }
        elif exp_obj:
            exception = cls.exception_handler(exp_obj)
            Resp['errorDetail'] = exception
            if not message:
                message = exception.get('exception')
        else:
            Resp['data'] = data
        Resp['message'] = message if message else code_type.name
        if kwargs:
            for key, value in kwargs.items():
                Resp[str(key)] = value
        return Resp

    @classmethod
    def exception_handler(clsm, exp_obj):
        tb_next = exp_obj[2].tb_next
        while tb_next:
            if not tb_next.tb_next:
                break
            else:
                tb_next = tb_next.tb_next
        if tb_next:
            tb_frame = tb_next.tb_frame
            filename = tb_frame.f_code.co_filename
            func_name = tb_frame.f_code.co_name
            lineno = tb_frame.f_lineno
        else:
            filename = ""
            func_name = ""
            lineno = ""
        exception = exp_obj[0].__name__ + ":" + str(exp_obj[1]).replace("'", '')
        return {"file": filename, "function": func_name,
                "lineNo": lineno, "exception": exception
                }

    @classmethod
    def key_validate(cls, data, node_name):
        '''
        针对A.B.C　的字符串类型进行递归判断,如果不存在相应字段,返回相应错误
        :param data:
        :type data: dict
        :param node_name:
        :type node_name: str
        :return:
        :rtype:
        '''
        key_list = node_name.split('.')
        if not isinstance(data, dict):
            return cls.format_Resp(code_type=CodeStatus.InvalidDataError, message='parameter data must be dict')
        try:
            for index, key in enumerate(key_list):
                match_res = re.findall(r'(.*)\[(.+?)\]', key)
                if match_res:
                    k1, index1 = match_res[0][0], match_res[0][1]
                    if not k1:
                        return cls.format_Resp(code_type=CodeStatus.ParametersMissError,
                                               message="{} doesn't exists".format(k1))

                    data = data[k1][int(index1)]
                else:
                    data = data[key]
            return cls.format_Resp(data=data)
        except:
            exp = sys.exc_info()
            return Util.format_Resp(code_type=CodeStatus.UnknownError, exc_obj=exp)

    @classmethod
    def get_now(cls, formatStr='%Y-%m-%d %H:%M:%S'):
        return datetime.now().strftime(formatStr)

    @classmethod
    def get_utc_time(cls):
        return datetime.utcnow()

    @classmethod
    def datetime_to_str(cls, obj, formatStr="%Y-%m-%d"):
        return obj.strftime(formatStr)

    @classmethod
    def str_to_datetime(cls, string, formatStr="%Y-%m-%d"):
        return datetime.strptime(string, formatStr)

    @classmethod
    def gen_md5_hash(cls, text):
        '''
        Generates md5 hash.
        :param obj:
        :return: Encoded string.
        '''
        return hashlib.md5(text.encode(encoding='utf-8')).hexdigest()

    @classmethod
    def get_now_timestamp(cls, ms=True):
        if ms:
            return int(time.time() * 1000)
        return int(time.time())

    @staticmethod
    def replace_char(old_string, char, index):
        '''
        字符串按索引位置替换字符
        '''
        old_string = str(old_string)
        # 新的字符串 = 老字符串[:要替换的索引位置] + 替换成的目标字符 + 老字符串[要替换的索引位置+1:]
        new_string = old_string[:index] + char + old_string[index + 1:]
        return new_string

    @staticmethod
    def filter_null(data):
        newDict = {}
        for k, v in data.items():
            if v != None:
                newDict[k] = v
        return newDict

    @classmethod
    def timeStamp_to_datetime(cls, timeStamp, formatStr='%Y-%m-%d %H:%M:%S'):
        length = len(str(timeStamp))
        if length == 13:
            return time.strftime(formatStr, time.localtime(int(timeStamp) / 1000))
        return time.strftime(formatStr, time.localtime(int(timeStamp)))


class OSS:
    endpoint = settings.OSS_ENDPOINT
    auth = asyncoss.Auth(settings.OSS_APIKEY, settings.OSS_APISECRET)
    bucketName = settings.OSS_BUCKETNAME

    @classmethod
    async def upload(cls, fileObj=None, path=None, request=None, content=None):
        '''

        :param fileObj:
        :param path:
        :param request: 获取customerId、stationId
        :param content: file stream
        :return:
        '''
        async with asyncoss.Bucket(cls.auth, cls.endpoint, cls.bucketName) as bucket:
            basePath = f"{Util.get_now('%Y%m%d')}/{request.state.openid}"
            if content:
                fullFileName = "{}/{}".format(
                    basePath, path)
            else:
                suffix = fileObj.filename.split(".")[-1]
                fileName = Util.gen_md5_hash("{}+{}".format(fileObj.filename, time()))
                fullFileName = f"{basePath}/{fileName}.{suffix}"
                content = fileObj.file.read()
            await bucket.put_object(fullFileName, content)
            return fullFileName

    @classmethod
    async def download(cls, fileName):
        async with asyncoss.Bucket(cls.auth, cls.endpoint, cls.bucketName) as bucket:
            result = await bucket.get_object(fileName)
            await result.resp.read()

    @classmethod
    async def delete(cls, fileName):
        async with asyncoss.Bucket(cls.auth, cls.endpoint, cls.bucketName) as bucket:
            await bucket.delete_object(fileName)
            return Util.format_Resp(message="delete successfully")

    @classmethod
    def get_temp_url(cls, objName):
        bucket = oss2.Bucket(cls.auth, cls.endpoint, cls.bucketName)
        return bucket.sign_url('GET', objName, int(os.getenv("STATIC_FILE_EXPIRED_TIME", 600)))
