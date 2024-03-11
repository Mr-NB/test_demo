from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from app.util import Util
from app.mapping import CodeStatus
from app.core.config import settings
from app.core.security import verify_token

app = FastAPI(title=settings.PROJECT_NAME, description=settings.PROJECT_DESCRIPTION, version=settings.PROJECT_VERSION)

app.mount("/static", StaticFiles(directory="static"), name="static")
# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


app.state.ws_manager = ConnectionManager()


# 请求中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    headers = request.headers
    Authorization = headers.get("token")
    path = request.scope.get("path", "")
    if path.startswith(settings.API_V1_STR) and "login" not in path and "untoken" not in path:
        if not Authorization:
            return JSONResponse(Util.format_Resp(code_type=CodeStatus.Unauthorized, message="Invalid Token"))
        if not Authorization.startswith("Bearer"):
            return JSONResponse(Util.format_Resp(code_type=CodeStatus.Unauthorized, message="Invalid Token"))
        # {'exp': 1709876967, 'sub': 'o3YMd6DenAuENxZTqqLn39lSCk9w'}
        verify_res = verify_token(Authorization)
        if verify_res.get("code") != 200:
            return JSONResponse(verify_res)
        request.state.openid = verify_res.get("data", {}).get("sub")
    # request.state.token = Authorization

    response = await call_next(request)
    if response.status_code == 422:
        return JSONResponse(Util.format_Resp(code_type=CodeStatus.ParameterTypeError, message="Parameter type error"))
    return response


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     error_messages = []
#     for error in exc.errors():
#         error_messages.append({
#             'loc': error['loc'],
#             'msg': error['msg'],
#             'type': error['type']
#         })
#     raise HTTPException(status_code=422, detail={'errors': error_messages})
# @app.exception_handler(ValidationError)
# async def integrity_error_handler(request, exc: ValidationError):
#     return JSONResponse(
#         status_code=400,
#         content={'error_code': 40001, 'error_message': 'Data integrity error.'},
#     )

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.status_code, "data": "", "message": str(exc.detail)},
    )


app.add_exception_handler(HTTPException, custom_http_exception_handler)


# 捕获所有其他异常
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    # traceback_str = ''.join(traceback.format_tb(exc.__traceback__))  # or you can log the traceback here
    return JSONResponse(
        status_code=200,
        content=Util.format_Resp(code_type=CodeStatus.UnknownError, message=exc.__str__())
    )
