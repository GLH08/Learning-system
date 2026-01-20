from pydantic import BaseModel, Field


class InitRequest(BaseModel):
    password: str = Field(..., min_length=6, description="管理员密码，至少6位")


class LoginRequest(BaseModel):
    password: str = Field(..., description="管理员密码")


class LoginResponse(BaseModel):
    token: str
    expiresIn: int


class VerifyResponse(BaseModel):
    valid: bool
    initialized: bool


class ChangePasswordRequest(BaseModel):
    oldPassword: str = Field(..., description="原密码")
    newPassword: str = Field(..., min_length=6, description="新密码，至少6位")
