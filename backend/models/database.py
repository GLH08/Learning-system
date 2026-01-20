from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from config import settings

# Ensure data directory exists (only for file-based operations)
if settings.DATA_DIR and not settings.DATABASE_URL.startswith('postgresql'):
    os.makedirs(settings.DATA_DIR, exist_ok=True)

# Create engine with appropriate connect_args
connect_args = {}
if settings.DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with tables and default data"""
    from models import category, question, exam, ai_task, learning_stat, setting
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize default settings
    db = SessionLocal()
    try:
        from models.setting import Setting
        
        default_settings = [
            ("admin_password_hash", "", "管理员密码哈希值"),
            ("ai_api_url", "https://api.openai.com/v1", "AI API基础地址"),
            ("ai_api_key", "", "AI API密钥"),
            ("ai_model", "gpt-4o-mini", "AI模型名称"),
            ("ai_max_tokens", "2000", "AI单次请求最大token数"),
            ("ai_temperature", "0.7", "AI生成温度参数"),
            ("site_title", "智能答题学习系统", "网站标题"),
            ("default_exam_time", "60", "默认考试时间(分钟)"),
            ("auto_collect_wrong", "true", "是否自动收集错题"),
            ("initialized", "false", "系统是否已初始化"),
        ]
        
        for key, value, description in default_settings:
            existing = db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                setting = Setting(key=key, value=value, description=description)
                db.add(setting)
        
        # Create default category
        from models.category import Category
        default_cat = db.query(Category).filter(Category.id == "default").first()
        if not default_cat:
            default_category = Category(
                id="default",
                name="未分类",
                description="默认分类，用于存放未分类的题目",
                sort_order=999
            )
            db.add(default_category)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()


def get_settings(db):
    """Get all settings as a dictionary"""
    from models.setting import Setting
    
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}


def update_settings(db, settings_dict):
    """Update multiple settings"""
    from models.setting import Setting
    
    for key, value in settings_dict.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            new_setting = Setting(key=key, value=str(value))
            db.add(new_setting)
    
    db.commit()
