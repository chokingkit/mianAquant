"""
API v1 端点模块
包含所有 v1 版本的 API 端点路由
"""
from fastapi import APIRouter
from app.api.v1.endpoints import stock, calendar, strategy, backtest, tasks, risk

# 创建主路由
router = APIRouter(prefix="/api/v1")

router.include_router(stock.router, prefix="/stocks", tags=["股票数据"])
router.include_router(calendar.router, prefix="/calendar", tags=["交易日历"])
router.include_router(strategy.router, prefix="/strategies", tags=["策略管理"])
router.include_router(backtest.router, prefix="/backtest", tags=["回测"])
router.include_router(tasks.router, prefix="/tasks", tags=["异步任务"])
router.include_router(risk.router, prefix="/risk", tags=["风险管理"])

__all__ = ['router']
