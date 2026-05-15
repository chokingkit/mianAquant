"""
API v1 版本模块
初始化 v1 版本的 API 路由
"""
from fastapi import APIRouter
from app.api.v1.endpoints import stock, calendar

# 创建 v1 路由
v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(stock.router, prefix="/stocks", tags=["股票数据"])
v1_router.include_router(calendar.router, prefix="/calendar", tags=["交易日历"])

__all__ = ['v1_router']
