import os
import json
from datetime import timedelta
from time import time
import hashlib
import hmac
import urllib

import base64
from Crypto.Cipher import AES
from fastapi import HTTPException
import asyncio
import aiofiles

from app.lib import Lib
from app.util import Util, OSS
from app.mapping import CodeStatus
from app.models.model import User
from app.core.config import settings
from app.core import security
from app import app
from app.models.model import Message


class MiniProgram:

    @classmethod
    async def get_openId(cls, code):
        # 通过code 获取 openId
        url = "https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code".format(
            settings.MINI_PRAGRAM_APPID, settings.MINI_PRAGRAMAPP_SECRET,
            code)
        return await Lib.Request(endpoint=url, detail=False)

    @classmethod
    async def login_access_token(cls, data):
        '''
        :param data:
        :return:
        '''
        getRes = await cls.get_openId(data.get('code'))
        # encryptedData = data.get('encryptedData')
        # iv = data.get('iv')
        if isinstance(getRes, str):
            getRes = json.loads(getRes)
        if getRes.get('errcode'):
            return Util.format_Resp(code_type=CodeStatus.BadRequest, message=getRes.get('errmsg'))
        sessionKey = getRes.get('session_key')
        openId = getRes.get('openid')
        # {'nickName': '微信用户', 'gender': 0, 'language': '', 'city': '', 'province': '', 'country': '', 'avatarUrl': 'https://thirdwx.qlogo.cn/mmopen/vi_32/POgEwh4mIHO4nibH0KlMECNjjGxQUq24ZEaGT4poC6icRiccVGKSyXwibcPq4BWmiaIGuG1icwxaQX6grC9VemZoJ8rg/132', 'watermark': {'timestamp': 1709142535, 'appid': 'wxcd3ad6e496aedde6'}, 'is_demote': True}
        # decrypt_res = cls.decrypt(sessionKey, encryptedData, iv)
        nickname = data.get("nickname")
        avatar_url = data.get("avatar_url")
        userObj = await User.get_or_none(openid=openId)
        user_data = {"nickname": nickname, "avatar_url": avatar_url,
                     "openid": openId}
        if not userObj:
            await User.add(user_data)
        else:
            if nickname and avatar_url:
                user_data['id'] = userObj.id
                await userObj.update(user_data)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = security.create_access_token(
            openId
        )
        token_bearer = f"Bearer {access_token}"
        # await app.redis.setex(f"token:{openId}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, token_bearer)
        await app.redis.set(f"token:{openId}", token_bearer)
        return Util.format_Resp(data={"token": token_bearer, "nickname": nickname, "avatar_url": avatar_url})

    @classmethod
    async def login_auth(cls, code):
        getRes = await cls.get_openId(code)
        if isinstance(getRes, str):
            getRes = json.loads(getRes)
        if getRes.get('errcode'):
            return Util.format_Resp(code_type=CodeStatus.BadRequest, message=getRes.get('errmsg'))
        sessionKey = getRes.get('session_key')
        openId = getRes.get('openid')
        cache_token = await app.redis.get(f"token:{openId}")

        user_obj = await User.get_or_none(openid=openId)
        if not user_obj:
            return Util.format_Resp(code_type=CodeStatus.Unauthorized, message="需要绑定")
        else:
            if not cache_token:
                cache_token = security.create_access_token(openId)
                # return Util.format_Resp(code_type=CodeStatus.Unauthorized, message="需要授权")
            return Util.format_Resp(
                data={"token": cache_token, "nickname": user_obj.nickname, "avatar_url": user_obj.avatar_url})

    @classmethod
    def decrypt(cls, sessionKey, encryptedData, iv):
        '''
        通过sessionKey + encryptedData + iv 解密用户信息
        '''
        sessionKey = base64.b64decode(sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)
        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)
        unpad = cipher.decrypt(encryptedData)

        return json.loads(unpad[:-ord(unpad[len(unpad) - 1:])])

    # def send_messageTemplate(self, data):


class Minimax:

    @classmethod
    async def chat_completion_pro(cls, sender_name, message, session_id=None):
        url = "https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId=" + settings.MINIMAX_GROUP_ID
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + settings.MINIMAX_APIKEY}

        cur_message = {"sender_type": "USER", "sender_name": sender_name, "text": message}
        message_list = []
        bot_name = settings.MINIMAX_BOT_NAME
        if session_id:
            history_list = (await Message.get_all(filterParams={"session_id": session_id})).get("data")

            for item in history_list:
                openid = item.get("openid")
                message_list.append(
                    {"sender_type": "USER" if openid else "BOT", "sender_name": openid if openid else bot_name,
                     "text": item.get("message")})
            message_list.append(cur_message)
        else:
            message_list.append(cur_message)

        payload = {
            "bot_setting": [
                {
                    "bot_name": bot_name,
                    "content": "MM智能助理要扮演一个美国人，只能用英文回复",
                }
            ],
            "messages": message_list,
            "reply_constraints": {"sender_type": "BOT", "sender_name": bot_name},
            "model": settings.MINIMAX_MODEL,
            "tokens_to_generate": settings.MINIMAX_TOKEN_NUM,
            "temperature": settings.MINIMAX_TEMPERATURE,
            "top_p": settings.MINIMAX_TOP_P,
        }

        response = await Lib.Request(endpoint=url, headers=headers, json=payload, methods="post", detail=False)
        base_resp = response.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise HTTPException(status_code=CodeStatus.Forbidden.value,
                                detail=f"MINIMAX ERROR:{base_resp.get('status_msg')}")
        return response

    @classmethod
    async def open_topic(cls, openid):
        return await cls.chat_completion_pro(openid, "开启一个有趣的话题")

    @classmethod
    async def handle_task(cls, session_id, openid, question, audio=False):
        answer = await cls.chat_completion_pro(openid, question, session_id)
        # cache = await app.redis.get(session_id)
        reply = answer.get("reply")
        # new_dialogue_list = json.loads(cache)

        bot_chat_id = Util.gen_md5_hash(f"bot{str(time())}")

        await Message.add({"message": reply, "session_id": session_id, "chat_id": bot_chat_id})
        # new_dialogue_list.extend(
        #     [{"sender": sender_name, "message": question, "chat_id": user_chat_id, "message_type": "audio",
        #       "created_time": Util.get_now()},
        #      {"sender": "bot", "message": reply, "chat_id": bot_chat_id, "created_time": Util.get_now()}])
        # if audio:
        #     await app.redis.set(f"audio:{user_chat_id}", question)
        # await app.redis.set(session_id, json.dumps(new_dialogue_list))
        return {"session_id": session_id, "reply": reply, "bot_chat_id": bot_chat_id}


class XunFei(object):
    def __init__(self, appid=settings.XUNFEI_VOICE_TRANSCRIPTION_APPID,
                 secret_key=settings.XUNFEI_VOICE_TRANSCRIPTION_APISECRET):
        self.appid = appid
        self.secret_key = secret_key
        self.ts = str(int(time()))
        self.signa = self.get_signa()
        self.error_mapping = {"1": "音频上传失败", "2": "音频转码失败", "3": "音频识别失败", "4": "音频时长超限（最大音频时长为 5 小时）",
                              "5": "音频校验失败（duration 对应的值与真实音频时长不符合要求）", "6": "静音文件", "7": "翻译失败", "8": "账号无翻译权限",
                              "9": "转写质检失败", "10": "转写质检未匹配出关键词",
                              "11": "upload接口创建任务时，未开启质检或者翻译能力,备注：resultType=translate，未开启翻译能力；resultType=predict，未开启质检能力；"}
        self.task_estimate_time = 0

    def get_signa(self):
        appid = self.appid
        secret_key = self.secret_key
        m2 = hashlib.md5()
        m2.update((appid + self.ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
        signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        return signa

    async def upload(self, file, callback=False, language="cn"):
        data = await file.read()
        filename = file.filename
        filelen = len(data)
        param_dict = {"appId": self.appid, "signa": self.signa, "ts": self.ts, "fileSize": filelen,
                      "fileName": filename, "duration": filelen, "eng_smoothproc": False, "eng_colloqproc": False,
                      "language": language}
        if callback:
            param_dict["callbackUrl"] = settings.XUNFEI_CALLBACK_URL
        response = await Lib.Request(endpoint=f"{settings.XUNFEI_HOST}/upload?{urllib.parse.urlencode(param_dict)}",
                                     headers={"Content-type": "application/json"}, methods="post", data=data,
                                     detail=False)

        if response.get("code") != "000000":
            # {
            #  "code": "26600",
            #  "descInfo": "转写业务通用错误"
            # }
            raise HTTPException(status_code=CodeStatus.Forbidden.value,
                                detail=f"XUNFEI ERROR:{response.get('descInfo')}")
        '''
        {
         "code": "000000",
         "descInfo": "success",
         "content": {
          "orderId": "DKHJQ202209021522090215490FAAE7DD0008C",
          "taskEstimateTime": 28000
         }
        }
        '''
        content = response.get("content")
        self.task_estimate_time = content.get("taskEstimateTime") / 1000

        return content

    # async def get_transfer_result_loop(self, orderId):
    #     param_dict = {"appId": self.appid, "signa": self.signa, "ts": self.ts, "orderId": orderId,
    #                   "duration": "200"}
    #     status = 3
    #     # 建议使用回调的方式查询结果，查询接口有请求频率限制
    #     while status == 3:
    #         response = await Lib.Request(
    #             endpoint=f"{settings.XUNFEI_HOST}/getResult?{urllib.parse.urlencode(param_dict)}",
    #             headers={"Content-type": "application/json"}, methods="post", detail=False)
    #
    #         # 0：订单已创建 3：订单处理中 4：订单已完成 -1：订单失败
    #         order_info = response.get("content", {}).get("orderInfo", {})
    #         status = order_info.get("status")
    #         # 0：音频正常执行 1：音频上传失败 2：音频转码失败 3：音频识别失败 4：音频时长超限（最大音频时长为 5 小时）5：音频校验失败（duration 对应的值与真实音频时长不符合要求）
    #         # 6：静音文件 7：翻译失败 8：账号无翻译权限 9：转写质检失败 10：转写质检未匹配出关键词 11：upload接口创建任务时，未开启质检或者翻译能力；
    #         # 备注：
    #         fail_type = order_info.get("failType")
    #         order_result = response.get("content", {}).get("orderResult")
    #         if status == 4:
    #             text = ""
    #             transfer_result = json.loads(order_result).get("lattice", [])
    #             for item in transfer_result:
    #                 # 每段
    #                 json_item = json.loads(item.get("json_1best"))
    #                 data_list = json_item.get("st", {}).get("rt", [])[0].get("ws")
    #                 for dItem in data_list:
    #                     text += dItem.get("cw", [])[0].get("w")
    #                 text += ""
    #             return Util.format_Resp(data={"content": text, "estimate_time": self.task_estimate_time})
    #         if status == -1:
    #             raise HTTPException(status_code=CodeStatus.Forbidden.value,
    #                                 detail=f"XUNFEI ERROR:{self.error_mapping.get(str(fail_type))}")
    #         await asyncio.sleep(settings.AUDIO_DELAY)

    async def get_transfer_result_loop(self, orderId):

        while True:
            if await app.redis.get(f"audio:task:{orderId}"):
                break
            await asyncio.sleep(settings.WS_LOOP_TIME)
        return await self.get_transfer_result(orderId)

    async def get_transfer_result(self, orderId):
        param_dict = {"appId": self.appid, "signa": self.signa, "ts": self.ts, "orderId": orderId,
                      "duration": "200"}
        response = await Lib.Request(
            endpoint=f"{settings.XUNFEI_HOST}/getResult?{urllib.parse.urlencode(param_dict)}",
            headers={"Content-type": "application/json"}, methods="post", detail=False)
        if response.get("code") != "000000":
            raise HTTPException(status_code=CodeStatus.Forbidden.value,
                                detail=f"XUNFEI ERROR:{json.dumps(response)}")
        order_result = response.get("content", {}).get("orderResult")
        text = ""
        transfer_result = json.loads(order_result).get("lattice", [])
        for item in transfer_result:
            # 每段
            json_item = json.loads(item.get("json_1best"))
            data_list = json_item.get("st", {}).get("rt", [])[0].get("ws")
            for dItem in data_list:
                text += dItem.get("cw", [])[0].get("w")
            text += ""
        return Util.format_Resp(data=text)

    async def voice_transfer(self, file, language):
        uploadresp = await self.upload(file, language=language, callback=True)
        orderId = uploadresp.get("orderId")
        return await self.get_transfer_result_loop(orderId)

    async def rapid_voice_transfer(self):
        pass

    # def handle_transfer_result(self,data):
    #     data.get("")
