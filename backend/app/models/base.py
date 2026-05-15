"""
数据库模型基类
提供共享的 Base 和 engine，确保模型在同一元数据内
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.config import get_settings

settings = get_settings()

# 共享的 Base（所有模型必须导入此 Base）
Base = declarative_base()

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # 检查连接是否有效
    pool_recycle=3600  # 连接回收时间（秒）
)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info(f"✓ 数据库引擎初始化: {settings.database_url}")


def get_db():
    """
    获取数据库会话（依赖注入）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建所有数据库表
    """
    Base.metadata.create_all(bind=engine)
    logger.info("✓ 数据库表创建完成")


def drop_tables():
    """
    删除所有数据库表（慎用！）
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠ 数据库表已删除")


def get_engine():
    """
    获取数据库引擎
    """
    return engine


def get_session_local():
    """
    获取 SessionLocal 类
    """
    return SessionLocal
