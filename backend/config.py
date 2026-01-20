from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str
    
    # CORS - 支持逗号分隔的字符串或JSON数组
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # File paths (for backup and file uploads)
    DATA_DIR: str = "/tmp"
    BACKUP_DIR: str = "/tmp/backup"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS


settings = Settings()
