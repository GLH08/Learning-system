from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.setting import Setting
from schemas.auth import (
    InitRequest, LoginRequest, LoginResponse,
    VerifyResponse, ChangePasswordRequest
)
from schemas.common import Response
from utils.security import (
    verify_password, get_password_hash,
    create_access_token, get_current_user
)
from utils.exceptions import PasswordError, AlreadyExistsError
from config import settings

router = APIRouter()


@router.post("/init", response_model=Response[LoginResponse])
async def initialize(request: InitRequest, db: Session = Depends(get_db)):
    """Initialize admin password (first time setup)"""
    # Check if already initialized
    initialized = db.query(Setting).filter(Setting.key == "initialized").first()
    if initialized and initialized.value == "true":
        raise AlreadyExistsError("系统已初始化，请直接登录")
    
    # Hash password
    password_hash = get_password_hash(request.password)
    
    # Save password hash
    password_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if password_setting:
        password_setting.value = password_hash
    else:
        password_setting = Setting(key="admin_password_hash", value=password_hash)
        db.add(password_setting)
    
    # Mark as initialized
    if initialized:
        initialized.value = "true"
    else:
        initialized = Setting(key="initialized", value="true")
        db.add(initialized)
    
    db.commit()
    
    # Generate token
    token = create_access_token(data={"sub": "admin"})
    
    return Response(
        code=0,
        message="初始化成功",
        data=LoginResponse(
            token=token,
            expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/login", response_model=Response[LoginResponse])
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login"""
    # Get password hash from database
    password_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if not password_setting or not password_setting.value:
        raise PasswordError("系统未初始化，请先设置密码")
    
    # Verify password
    if not verify_password(request.password, password_setting.value):
        raise PasswordError("密码错误")
    
    # Generate token
    token = create_access_token(data={"sub": "admin"})
    
    return Response(
        code=0,
        message="登录成功",
        data=LoginResponse(
            token=token,
            expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/logout", response_model=Response)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout (client should remove token)"""
    return Response(code=0, message="登出成功")


@router.get("/verify", response_model=Response[VerifyResponse])
async def verify(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Verify token validity"""
    initialized = db.query(Setting).filter(Setting.key == "initialized").first()
    is_initialized = initialized and initialized.value == "true"
    
    return Response(
        code=0,
        message="success",
        data=VerifyResponse(valid=True, initialized=is_initialized)
    )


@router.put("/password", response_model=Response)
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change admin password"""
    # Get current password hash
    password_setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if not password_setting or not password_setting.value:
        raise PasswordError("密码未设置")
    
    # Verify old password
    if not verify_password(request.oldPassword, password_setting.value):
        raise PasswordError("原密码错误")
    
    # Update password
    password_setting.value = get_password_hash(request.newPassword)
    db.commit()
    
    return Response(code=0, message="密码修改成功")
