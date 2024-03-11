from enum import Enum


class CodeStatus(Enum):
    SuccessCode = 200
    Unauthorized = 401
    Unbind = 402
    Forbidden = 403
    NotFound = 404
    BadRequest = 400

    UnknownError = 500
    ParameterTypeError = 422
    Timeout = 504
    CmsUndoPublishError = 156
    PermissionDenied = 104
    FormatError = 105
    ParametersMissError = 106
    ParametersTypeError = 107
    InvalidDataError = 108
    DataDuplicateError = 109
