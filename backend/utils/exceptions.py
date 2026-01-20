from fastapi import HTTPException, status


class QuizException(HTTPException):
    """Base exception for quiz system"""
    def __init__(self, code: int, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        self.code = code


class ParameterError(QuizException):
    """Parameter validation error"""
    def __init__(self, message: str = "参数错误"):
        super().__init__(code=40001, message=message)


class NotFoundError(QuizException):
    """Resource not found error"""
    def __init__(self, message: str = "数据不存在"):
        super().__init__(code=40002, message=message)


class AlreadyExistsError(QuizException):
    """Resource already exists error"""
    def __init__(self, message: str = "数据已存在"):
        super().__init__(code=40003, message=message)


class UnauthorizedError(QuizException):
    """Unauthorized error"""
    def __init__(self, message: str = "未登录或Token无效"):
        super().__init__(code=40101, message=message)
        self.status_code = status.HTTP_401_UNAUTHORIZED


class PasswordError(QuizException):
    """Password error"""
    def __init__(self, message: str = "密码错误"):
        super().__init__(code=40103, message=message)


class ServerError(QuizException):
    """Server internal error"""
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(code=50001, message=message)
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class AIServiceError(QuizException):
    """AI service error"""
    def __init__(self, message: str = "AI服务调用失败"):
        super().__init__(code=50002, message=message)


class FileParseError(QuizException):
    """File parsing error"""
    def __init__(self, message: str = "文件解析失败"):
        super().__init__(code=50003, message=message)
