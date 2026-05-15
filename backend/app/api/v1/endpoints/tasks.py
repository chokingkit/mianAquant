"""
任务管理 API
提供任务提交、状态查询、取消任务等接口
"""
from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db

# 惰性导入 celery，未安装时使用降级模式
_CELERY_AVAILABLE = False
AsyncResult = None
celery_app = None
run_backtest_task = None

try:
    from celery.result import AsyncResult  # noqa: F401
    from app.tasks.celery_app import celery_app
    from app.tasks.backtest_tasks import run_backtest_task
    _CELERY_AVAILABLE = True
except Exception:
    pass

from app.models.backtest import BacktestResult

router = APIRouter(prefix="/tasks", tags=["异步任务"])


@router.post("/backtest/submit", summary="提交回测任务")
def submit_backtest_task(strategy_id: int,
                         start_date: str,
                         end_date: str,
                         initial_cash: float = 100000.0,
                         stock_pool: Optional[list] = None,
                         db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    提交异步回测任务
    
    Args:
        strategy_id: 策略配置 ID
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        initial_cash: 初始资金
        stock_pool: 股票池（可选）
        db: 数据库会话
        
    Returns:
        Dict: 任务信息（task_id, backtest_id）
    """
    if not _CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="异步任务功能不可用：Celery 未安装")
    # 验证策略是否存在
    from app.models.strategy import StrategyConfig
    strategy_config = db.query(StrategyConfig).filter(
        StrategyConfig.id == strategy_id
    ).first()
    
    if not strategy_config:
        raise HTTPException(status_code=404, detail=f"策略未找到: ID={strategy_id}")
    
    # 提交异步任务
    task = run_backtest_task.delay(
        strategy_id=strategy_id,
        start_date_str=start_date,
        end_date_str=end_date,
        initial_cash=initial_cash,
        stock_pool=stock_pool
    )
    
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "回测任务已提交"
    }


@router.get("/backtest/{task_id}", summary="查询回测任务状态")
def get_backtest_task_status(task_id: str) -> Dict[str, Any]:
    """
    查询回测任务状态
    
    Args:
        task_id: Celery 任务 ID
        
    Returns:
        Dict: 任务状态信息
    """
    if not _CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="异步任务功能不可用：Celery 未安装")
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.state,
    }
    
    if task_result.state == "PENDING":
        response["message"] = "任务等待中"
    elif task_result.state == "PROGRESS":
        response["meta"] = task_result.info.get("meta", {})
        response["message"] = task_result.info.get("status", "正在执行...")
    elif task_result.state == "SUCCESS":
        response["result"] = task_result.result
        response["message"] = "任务完成"
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)
        response["message"] = "任务失败"
    else:
        response["message"] = f"任务状态: {task_result.state}"
    
    return response


@router.delete("/backtest/{task_id}", summary="取消回测任务")
def cancel_backtest_task(task_id: str) -> Dict[str, Any]:
    """
    取消回测任务
    
    Args:
        task_id: Celery 任务 ID
        
    Returns:
        Dict: 取消结果
    """
    if not _CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="异步任务功能不可用：Celery 未安装")
    celery_app.control.revoke(task_id, terminate=True, signal="SIGKILL")
    
    return {
        "task_id": task_id,
        "status": "revoked",
        "message": "任务已取消"
    }


@router.get("/backtest/{task_id}/result", summary="获取回测任务结果")
def get_backtest_task_result(task_id: str,
                             db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取回测任务的结果（从数据库）
    
    Args:
        task_id: Celery 任务 ID
        db: 数据库会话
        
    Returns:
        Dict: 回测结果
    """
    if not _CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="异步任务功能不可用：Celery 未安装")
    # 先检查任务状态
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state != "SUCCESS":
        return {
            "task_id": task_id,
            "status": task_result.state,
            "message": "任务尚未完成"
        }
    
    # 获取任务结果中的 backtest_id
    result = task_result.result
    backtest_id = result.get("backtest_id")
    
    if not backtest_id:
        raise HTTPException(status_code=404, detail="回测结果未找到")
    
    # 从数据库查询完整结果
    backtest = db.query(BacktestResult).filter(
        BacktestResult.id == backtest_id
    ).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="回测结果未找到")
    
    return backtest.to_dict()


@router.get("/list", summary="列出所有任务")
def list_tasks(limit: int = 20,
               db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    列出最近的回测任务
    
    Args:
        limit: 返回数量限制
        db: 数据库会话
        
    Returns:
        Dict: 任务列表
    """
    results = db.query(BacktestResult).order_by(
        BacktestResult.created_at.desc()
    ).limit(limit).all()
    
    return {
        "total": len(results),
        "tasks": [r.to_dict() for r in results]
    }
