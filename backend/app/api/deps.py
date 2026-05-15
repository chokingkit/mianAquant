"""
API 依赖模块
提供依赖注入（如数据库会话）
"""
from typing import Generator
from loguru import logger

from app.models.base import engine, SessionLocal


def get_db() -> Generator:
    """
    获取数据库会话（依赖注入）
    
    Yields:
        Session: 数据库会话
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
    from app.models.base import Base
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    logger.info("✓ 数据库表创建完成")


def drop_tables():
    """
    删除所有数据库表（慎用！）
    """
    from app.models.base import Base
    
    # 删除表
    Base.metadata.drop_all(bind=engine)
    
    logger.warning("⚠ 数据库表已删除")
