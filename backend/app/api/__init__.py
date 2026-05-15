"""
API 模块
初始化 FastAPI 路由，注册所有 API 端点
"""
from fastapi import APIRouter
from app.api.v1.endpoints import stock, calendar

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(stock.router, prefix="/stocks", tags=["股票数据"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["交易日历"])

__all__ = ['api_router']
