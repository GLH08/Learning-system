"""
系统设置 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import shutil
import os
from datetime import datetime

from models.database import get_db, get_settings, update_settings
from services.ai_service import AIService, AIConfig
from api.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ============ Schemas ============

class AISettings(BaseModel):
    api_url: str
    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 8192  # 单次输出 token 限制，可根据模型调整


class SettingsResponse(BaseModel):
    ai_api_url: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None


class TestAIResponse(BaseModel):
    success: bool
    message: str


class BackupInfo(BaseModel):
    filename: str
    size: int
    created_at: str


# ============ API Endpoints ============

@router.get("", response_model=SettingsResponse)
def get_settings_api(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取系统设置"""
    settings = get_settings(db)
    
    return {
        "ai_api_url": settings.get("ai_api_url"),
        "ai_api_key": settings.get("ai_api_key"),
        "ai_model": settings.get("ai_model"),
        "ai_temperature": settings.get("ai_temperature"),
        "ai_max_tokens": settings.get("ai_max_tokens")
    }


@router.put("")
def update_settings_api(
    ai_settings: AISettings,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新系统设置"""
    
    # 更新设置
    update_settings(db, {
        "ai_api_url": ai_settings.api_url,
        "ai_api_key": ai_settings.api_key,
        "ai_model": ai_settings.model,
        "ai_temperature": ai_settings.temperature,
        "ai_max_tokens": ai_settings.max_tokens
    })
    
    return {"message": "设置已保存"}


@router.post("/test-ai", response_model=TestAIResponse)
async def test_ai_connection(
    ai_settings: AISettings,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """测试 AI 连接"""
    try:
        config = AIConfig(
            api_url=ai_settings.api_url,
            api_key=ai_settings.api_key,
            model=ai_settings.model,
            temperature=ai_settings.temperature,
            max_tokens=ai_settings.max_tokens
        )
        
        ai_service = AIService(config)
        success = ai_service.test_connection()  # 同步方法，不需要 await
        
        if success:
            return {
                "success": True,
                "message": "连接成功"
            }
        else:
            return {
                "success": False,
                "message": "连接失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}"
        }


@router.post("/backup", response_model=BackupInfo)
def create_backup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建数据备份"""
    try:
        # 创建备份目录
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制数据库文件
        db_path = "data/learning_system.db"
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="数据库文件不存在")
        
        shutil.copy2(db_path, backup_path)
        
        # 获取文件大小
        file_size = os.path.getsize(backup_path)
        
        return {
            "filename": backup_filename,
            "size": file_size,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.get("/backups")
def list_backups(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取备份列表"""
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # 按创建时间倒序排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.get("/backups/{filename}")
def download_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """下载备份文件"""
    try:
        backup_path = os.path.join("backups", filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        return FileResponse(
            backup_path,
            media_type="application/octet-stream",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """恢复备份"""
    try:
        # 验证文件类型
        if not file.filename.endswith(".db"):
            raise HTTPException(status_code=400, detail="只支持 .db 文件")
        
        # 保存上传的文件到临时位置
        temp_path = f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 备份当前数据库
        db_path = "data/learning_system.db"
        backup_current = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_current)
        
        # 关闭当前数据库连接
        db.close()
        
        # 替换数据库文件
        shutil.move(temp_path, db_path)
        
        return {
            "message": "恢复成功，请重启应用",
            "backup_current": backup_current
        }
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


@router.delete("/backups/{filename}")
def delete_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除备份文件"""
    try:
        backup_path = os.path.join("backups", filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        os.remove(backup_path)
        
        return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
