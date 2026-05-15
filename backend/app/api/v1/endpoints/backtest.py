"""
回测 API 端点
提供回测执行、结果查询 REST API
"""
from typing import Dict, Any, Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from loguru import logger

from app.models.backtest import BacktestResult
from app.services.backtest_service import BacktestService
from app.api.deps import get_db

router = APIRouter()


@router.post("/run", summary="运行回测")
async def run_backtest(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    运行回测
    
    Request Body:
        {
            "strategy_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_cash": 100000.0,
            "stock_pool": ["sh.600000", "sz.000001"]  # 可选，None 则使用策略配置中的股票池
        }
    """
    try:
        # 提取参数
        strategy_id = data.get("strategy_id")
        start_date = date.fromisoformat(data.get("start_date"))
        end_date = date.fromisoformat(data.get("end_date"))
        initial_cash = data.get("initial_cash", 100000.0)
        stock_pool = data.get("stock_pool")
        
        # 运行回测
        service = BacktestService(db)
        result = service.run_backtest(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            stock_pool=stock_pool
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Backtest execution failed")
        
        logger.info(f"✓ 回测完成: ID={result.id}, 收益率={result.total_return:.2%}")
        return {
            "code": 200,
            "message": "success",
            "data": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/results", summary="获取回测结果")
async def get_backtest_results(
    backtest_id: int = Path(..., description="回测结果 ID"),
    db: Session = Depends(get_db)
):
    """
    获取回测结果
    
    - **backtest_id**: 回测结果 ID
    """
    try:
        service = BacktestService(db)
        result = service.get_backtest_result(backtest_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Backtest result not found: ID={backtest_id}")
        
        logger.info(f"✓ 获取回测结果: ID={result.id}")
        return {
            "code": 200,
            "message": "success",
            "data": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="列出所有回测结果")
async def list_backtest_results(
    strategy_id: Optional[int] = Query(None, description="策略配置 ID（可选，用于过滤）"),
    status: Optional[str] = Query(None, description="状态过滤（pending/running/completed/failed）"),
    db: Session = Depends(get_db)
):
    """
    列出回测结果（支持过滤）
    
    - **strategy_id**: 可选，过滤策略配置 ID
    - **status**: 可选，过滤状态
    """
    try:
        service = BacktestService(db)
        results = service.list_backtest_results(strategy_id=strategy_id, status=status)
        
        result_list = [r.to_dict() for r in results]
        
        logger.info(f"✓ 列出回测结果: {len(result_list)} 个")
        return {
            "code": 200,
            "message": "success",
            "data": result_list
        }
    except Exception as e:
        logger.error(f"列出回测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{backtest_id}", summary="删除回测结果")
async def delete_backtest_result(
    backtest_id: int = Path(..., description="回测结果 ID"),
    db: Session = Depends(get_db)
):
    """
    删除回测结果
    
    - **backtest_id**: 回测结果 ID
    """
    try:
        service = BacktestService(db)
        success = service.delete_backtest_result(backtest_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Backtest result not found: ID={backtest_id}")
        
        logger.info(f"✓ 删除回测结果: ID={backtest_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"deleted": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除回测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/report", summary="生成回测报告")
async def generate_backtest_report(
    backtest_id: int = Path(..., description="回测结果 ID"),
    db: Session = Depends(get_db)
):
    """
    生成回测报告（文本格式）
    
    - **backtest_id**: 回测结果 ID
    """
    try:
        service = BacktestService(db)
        report = service.generate_report(backtest_id)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Backtest result not found: ID={backtest_id}")
        
        logger.info(f"✓ 生成回测报告: ID={backtest_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"report": report}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成回测报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/equity-curve", summary="获取权益曲线")
async def get_equity_curve(
    backtest_id: int = Path(..., description="回测结果 ID"),
    db: Session = Depends(get_db)
):
    """
    获取权益曲线数据（用于画图）
    
    - **backtest_id**: 回测结果 ID
    """
    try:
        service = BacktestService(db)
        result = service.get_backtest_result(backtest_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Backtest result not found: ID={backtest_id}")
        
        equity_curve = result.equity_curve or []
        
        logger.info(f"✓ 获取权益曲线: ID={result.id}, {len(equity_curve)} 个点")
        return {
            "code": 200,
            "message": "success",
            "data": {
                "backtest_id": backtest_id,
                "equity_curve": equity_curve
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取权益曲线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/trades", summary="获取交易记录")
async def get_trades(
    backtest_id: int = Path(..., description="回测结果 ID"),
    db: Session = Depends(get_db)
):
    """
    获取交易记录
    
    - **backtest_id**: 回测结果 ID
    """
    try:
        service = BacktestService(db)
        result = service.get_backtest_result(backtest_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Backtest result not found: ID={backtest_id}")
        
        trades = result.trades or []
        
        logger.info(f"✓ 获取交易记录: ID={result.id}, {len(trades)} 笔")
        return {
            "code": 200,
            "message": "success",
            "data": {
                "backtest_id": backtest_id,
                "total_trades": len(trades),
                "trades": trades
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
