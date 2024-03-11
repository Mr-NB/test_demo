import secrets
from typing import Any
import os

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "Ho5xwiSL0NMiohAg564EnWL3_erSPBTjaUY3MjQqV7A"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8)
    SERVER_HOST: AnyHttpUrl = os.getenv("SERVER_HOST", "http://0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 8084))
    SERVER_WORKERS: int = int(os.getenv("WORKERS", 4))

    MINI_PRAGRAM_APPID: str = os.getenv("MINI_PRAGRAM_APPID")
    MINI_PRAGRAMAPP_SECRET: str = os.getenv("MINI_PRAGRAM_APPSECRET")
    MYSQL_URI: str = os.getenv("MYSQL", "mysql://root:codeswitch@47.99.68.137:8004/codeswitch")
    TIME_ZONE: str = 'Asia/Shanghai'
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "自言自语")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "0.0.1")
    PROJECT_DESCRIPTION: str = os.getenv("PROJECT_DESCRIPTION", "AI口语练习")
    # class Config:
    #     case_sensitive = True
    REDIS_URI: str = os.getenv("REDIS", 'redis://47.99.68.137:8003')

    # minimax
    MINIMAX_GROUP_ID: str = os.getenv("MINIMAX_GROUP_ID")
    MINIMAX_APIKEY: str = os.getenv("MINIMAX_APIKEY")

    MINIMAX_MODEL: str = os.getenv("MINIMAX_MODEL", "abab5.5-chat")
    MINIMAX_TOKEN_NUM: int = os.getenv("MINIMAX_TOKEN_NUM", 1034)
    MINIMAX_BOT_NAME: str = os.getenv("MINIMAX_BOT_NAME", "字言")
    # 较高的值将使输出更加随机，而较低的值将使输出更加集中和确定。
    # abab5.5s 默认取值0.9 abab5.5 默认取值0.9 abab6 默认取值0.1
    # 低（0.01~0.2）：适合答案较明确的场景（如：知识问答、总结说明、情感分析、文本分类、大纲生成、作文批改）
    # ⾼（0.7〜1）：适合答案较开放发散的场景 （如：营销文案生成、人设对话）
    MINIMAX_TEMPERATURE: float = os.getenv("MINIMAX_TEMPERATURE", 0.9)
    # 采样方法，数值越小结果确定性越强；数值越大，结果越随机
    #  abab5.5s 默认取值0.95  abab5.5 默认取值0.95  abab6 默认取值0.9
    MINIMAX_TOP_P: float = os.getenv("MINIMAX_TOP_P", 0.95)

    XUNFEI_HOST = 'https://raasr.xfyun.cn/v2/api'
    XUNFEI_RAPID_VOICE_TRANSCRIPTION_APPID: str = os.getenv("XUNFEI_RAPID_VOICE_TRANSCRIPTION_APPID")
    XUNFEI_RAPID_VOICE_TRANSCRIPTION_APIKEY: str = os.getenv("XUNFEI_RAPID_VOICE_TRANSCRIPTION_APIKEY")
    XUNFEI_RAPID_VOICE_TRANSCRIPTION_APISECRET: str = os.getenv("XUNFEI_RAPID_VOICE_TRANSCRIPTION_APISECRET")
    XUNFEI_VOICE_TRANSCRIPTION_APPID: str = os.getenv("XUNFEI_VOICE_TRANSCRIPTION_APPID")
    XUNFEI_VOICE_TRANSCRIPTION_APISECRET: str = os.getenv("XUNFEI_VOICE_TRANSCRIPTION_APISECRET")
    XUNFEI_CALLBACK_URL: str = os.getenv("XUNFEI_CALLBACK_URL",
                                         "http://47.99.68.137:8084/api/v1/chat/untoken/audio-callback")
    AUDIO_DELAY: int = os.getenv("AUDIO_DELAY", 3)
    TEST_TOKEN: str = os.getenv("TEST_TOKEN",
                                "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvZHd1MTZ6bTFnZzUxUjl5cEZuWVIyNWV1bWFZIn0.OnNRVgXR2xEB8asb-DMvgCVO-Lm7DSpoGtJNCZvwbeY")
    WS_LOOP_TIME: int = os.getenv("WS_LOOP_TIME", 1)

    OSS_ENDPOINT = "http://oss-cn-beijing.aliyuncs.com"
    OSS_APIKEY: str = os.getenv("OSS_APIKEY")
    OSS_APISECRET = os.getenv("OSS_APISECRET")
    OSS_BUCKETNAME = "codeswitch-audio"


settings = Settings()
# print(secrets.token_urlsafe(32))
