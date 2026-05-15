"""
依赖注入模块
提供 FastAPI 依赖注入项
"""
from typing import AsyncGenerator, Optional
from functools import lru_cache

from fastapi import Depends, HTTPException
from app.config import Settings, get_settings


def get_settings_dependency() -> Settings:
    """获取配置依赖项"""
    return get_settings()


async def get_data_provider():
    """
    获取数据提供者依赖项
    后续实现：根据配置返回 Tushare 或 AKShare 数据提供者
    """
    settings = get_settings()
    provider_type = settings.data_provider.lower()
    
    if provider_type == "tushare":
        # TODO: 实现 TushareDataProvider
        raise HTTPException(
            status_code=501,
            detail="Tushare 数据提供者尚未实现"
        )
    elif provider_type == "akshare":
        # TODO: 实现 AKShareDataProvider
        raise HTTPException(
            status_code=501,
            detail="AKShare 数据提供者尚未实现"
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的数据源类型: {provider_type}"
        )


async def get_db_session():
    """
    获取数据库会话依赖项
    后续实现：返回 PostgreSQL 异步会话
    """
    # TODO: 实现数据库会话管理
    yield None
