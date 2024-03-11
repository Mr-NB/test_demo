from time import time
import json

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, Header, WebSocket
from typing_extensions import Annotated
from pydantic import BaseModel
from typing import Optional, Union
import asyncio

from app.views import Minimax, XunFei
from app.models.model import User, Message
from app.util import Util, OSS
from app import app
from app.core.config import settings
from app.mapping import CodeStatus

router = APIRouter()


@router.get(
    "/open_topic", name="对话-开启话题")
async def open_topic(request: Request):
    openid = request.state.openid
    session_id = Util.gen_md5_hash(str(time()))
    open_res = await Minimax.open_topic(openid)
    reply = open_res.get("reply")
    chat_id = Util.gen_md5_hash(f"{openid}{time()}")
    await Message.add({"message": reply, "session_id": session_id, "chat_id": chat_id})
    return Util.format_Resp(data={"session_id": session_id, "reply": reply})


class DialogueTextBody(BaseModel):
    session_id: str
    message: str


@router.post(
    "/text", name="对话-上传文本")
async def dialogue_text(request: Request, body: DialogueTextBody):
    openid = request.state.openid
    session_id, question = dict(body).get("session_id"), dict(body).get("message")
    user_chat_id = Util.gen_md5_hash(f"{openid}{time()}")
    await Message.add(
        {"message": question, "session_id": session_id, "chat_id": user_chat_id,
         "openid": openid})
    return await Minimax.handle_task(session_id, openid, question)


@app.post("/api/v1/chat/audio", name="对话-上传音频", tags=["chat"], description="language:cn：中文/en：英文/fr：法语/ko：韩语/ja：日语")
async def dialogue_audio(request: Request, token: str = Header(settings.TEST_TOKEN),
                         session_id: str = Form(""),
                         language: Optional[str] = Form("cn"), file: UploadFile = File("")):
    openid = request.state.openid
    transfer_res = await XunFei().voice_transfer(file, language)
    transfer_content = transfer_res.get("data", {})
    file_path = await OSS.upload(file, request=request)
    user_chat_id = Util.gen_md5_hash(f"{openid}{time()}")
    await Message.add(
        {"message": transfer_content, "session_id": session_id, "chat_id": user_chat_id,
         "source_url": file_path, "message_type": 2, "openid": openid})

    minimax_reply = await Minimax.handle_task(session_id, openid, transfer_content, audio=True)
    minimax_reply["user_chat_id"] = user_chat_id
    minimax_reply["transfer_content"] = transfer_content
    return Util.format_Resp(data=minimax_reply)


# @app.post("/api/v1/chat/audio", name="对话-上传音频")
# async def dialogue_audio(session_id: str, request: Request, file: UploadFile = File(...), token: str = Header(""),
#                          language: Optional[str] = "cn"):
#     '''
#     orderId：上传订单ID
#     taskEstimateTime 消耗时长
#     '''
#     return Util.format_Resp(data=await XunFei(file, language).upload())
#
#
# @app.post("/api/v1/chat/audio-upload", name="上传音频", tags=["chat"])
# async def audio_upload(request: Request,
#                        file: UploadFile = File(""), token: str = Header(settings.TEST_TOKEN)):
#     return await XunFei().upload(file, callback=True)


@app.get("/api/v1/chat/untoken/audio-callback", name="上传音频回调")
async def dialogue_audio_callback(orderId: str, status: str, resultType: str):
    '''
    orderId：上传订单ID
    status 识别状态 1(转写识别成功) 、-1(转写识别失败)
    '''
    await app.redis.set(f"audio:task:{orderId}", status)


# @router.get("/audio-callback-result", name="上传音频回调结果", description="status 识别状态 1(转写识别成功) 、-1(转写识别失败)")
# async def dialogue_audio_callback_result(orderId: str):
#     '''
#     orderId：上传订单ID
#     '''
#     res = await app.redis.get(f"audio:task:{orderId}")
#     if not res:
#         return Util.format_Resp(message="转换中")
#     return Util.format_Resp(data={"status": res})


# @router.get("/audio-transfer-result", name="上传音频转换结果")
# async def audio_transfer_result(orderId: str):
#     '''
#     orderId：上传订单ID
#     status 识别状态 1(转写识别成功) 、-1(转写识别失败)
#     '''
#     return await XunFei().get_transfer_result(orderId)


@router.get("/audio-to-text", name="对话-音频转文本", description="chat_id 通过/api/v1/chat/audio接口获取")
async def audio_to_text(chat_id: str):
    obj = await Message.get_or_none(chat_id=chat_id)
    if not obj:
        return Util.format_Resp(code_type=CodeStatus.NotFound, message="错误的chat_id")
    return Util.format_Resp(data=obj.message)


@app.websocket("/api/v1/chat/ws")
async def ws_audio(websocket: WebSocket, orderId: str):
    manager = app.state.ws_manager
    await manager.connect(websocket)
    print("xxxxx")
    try:
        while True:
            if await app.redis.get(f"audio:task:{orderId}"):

                await manager.send_personal_message(json.dumps(await XunFei().get_transfer_result(orderId)), websocket)
                manager.disconnect(websocket)
                break

            else:
                await manager.send_personal_message(json.dumps(Util.format_Resp(message="转换中...")), websocket)
            await asyncio.sleep(settings.WS_LOOP_TIME)
            # await manager.send_personal_message(json.dumps("xxxxx"), websocket)

    except Exception as e:
        manager.disconnect(websocket)


# @app.post("/uploadFile")
# async def create_file(
#         file: UploadFile = File(...),
#         fileName: str = Form(default=None),
#         dirPath: str = Form(...),
#         ossEndpoint: str = Form(default=None),
#         ossAk: str = Form(default=None),
#         ossAS: str = Form(default=None),
#         ossBucketName: str = Form(default=None),
#         md5: int = Form(default=1),
#         suffix: str = Form(default=None),
#         expires: int = Form(default=os.getenv("STATIC_FILE_EXPIRED_TIME", 999999999))
# ):

@router.get(
    "/dialogue—history", name="对话-历史", description="开启话题时，接口返回session_id,通过session_id可以查看对话历史")
async def dialogue_history(request: Request, session_id: str):
    return await Message.get_all(filterParams={"session_id": session_id})
# group_id = "1735116464916009499"
# api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZfoqIDoh6ror63vvIjmna3lt57vvInnp5HmioDmnInpmZDlhazlj7giLCJVc2VyTmFtZSI6IueOi-WuhyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzM1MTE2NDY0OTI0Mzk4MTA3IiwiUGhvbmUiOiIxNTI1MDU1ODkwOCIsIkdyb3VwSUQiOiIxNzM1MTE2NDY0OTE2MDA5NDk5IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDItMjIgMDA6NDM6MTciLCJpc3MiOiJtaW5pbWF4In0.tEsKEWOvZMh8Wrjflgni5QOrJp1cQ3j3lJ5fay__1Y08uFe2fNkexjNuf5r9yPOhheBwaevS4x8LO27tjItDSDPMck-Eo4pecWLBbQ3JZGkHr_OezDuJVN_GFqORNVdv91q-JVhInueyfAktJLL3eMsyILBHkBZHfOmKCj41SmNFwtrTOIJRf9YPLmzdQkvRakIDdmuwR5aUiXWh_aGlG6rTGtxPtDEatXPJktEYMl6r2w0-KMLV_rXyzxMxluNlS99VM37Oqf6SK6_CFvP-ma5WPpjGyGBAktwe0s_nS5WUfKbwRUXh6N9JZGko6zPgdLV57CIFMdrEGTZ6AuT6GQ"
#
# url = f"https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId={group_id}"
# headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
#
# # tokens_to_generate/bot_setting/reply_constraints可自行修改
# request_body = payload = {
#     "model": "abab5.5-chat",
#     "tokens_to_generate": 1024,
#     "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
#     "messages": [],
#     "bot_setting": [
#         {
#             "bot_name": "MM智能助理",
#             "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
#         }
#     ],
# }
# import requests
#
# # 添加循环完成多轮交互
# while True:
#     # 下面的输入获取是基于python终端环境，请根据您的场景替换成对应的用户输入获取代码
#     line = input("发言:")
#     # 将当次输入内容作为用户的一轮对话添加到messages
#     request_body["messages"].append(
#         {"sender_type": "USER", "sender_name": "小明", "text": line}
#     )
#     response = requests.post(url, headers=headers, json=request_body)
#     reply = response.json()["reply"]
#     print(f"reply: {reply}")
#     #  将当次的ai回复内容加入messages
#     request_body["messages"].extend(response.json()["choices"][0]["messages"])
