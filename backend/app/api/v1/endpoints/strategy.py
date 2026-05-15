"""
策略管理 API 端点
提供策略配置的增删改查 REST API
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from loguru import logger

from app.models.strategy import StrategyConfig
from app.services.strategy_service import StrategyService
from app.api.deps import get_db

router = APIRouter()


@router.post("/", summary="创建策略配置")
async def create_strategy(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建策略配置
    
    Request Body:
        {
            "name": "My MA Strategy",
            "strategy_type": "MAStrategy",
            "parameters": {"short_window": 5, "long_window": 20},
            "stock_pool": ["sh.600000", "sz.000001"],
            "description": "均线交叉策略",
            "is_active": true
        }
    """
    try:
        service = StrategyService(db)
        strategy = service.create_strategy(data)
        
        logger.info(f"✓ 创建策略配置: {strategy.name} (ID: {strategy.id})")
        return {
            "code": 200,
            "message": "success",
            "data": strategy.to_dict()
        }
    except Exception as e:
        logger.error(f"创建策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="列出所有策略配置")
async def list_strategies(
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    db: Session = Depends(get_db)
):
    """
    列出策略配置（支持过滤）
    
    - **strategy_type**: 可选，过滤策略类型（MAStrategy, MACDStrategy, RSIStrategy）
    - **is_active**: 可选，过滤激活状态
    """
    try:
        service = StrategyService(db)
        strategies = service.list_strategies(strategy_type=strategy_type, is_active=is_active)
        
        result = [s.to_dict() for s in strategies]
        
        logger.info(f"✓ 列出策略配置: {len(result)} 个")
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"列出策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", summary="获取策略配置详情")
async def get_strategy(
    strategy_id: int = Path(..., description="策略配置 ID"),
    db: Session = Depends(get_db)
):
    """
    获取策略配置详情
    
    - **strategy_id**: 策略配置 ID
    """
    try:
        service = StrategyService(db)
        strategy = service.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy not found: ID={strategy_id}")
        
        logger.info(f"✓ 获取策略配置: {strategy.name} (ID: {strategy.id})")
        return {
            "code": 200,
            "message": "success",
            "data": strategy.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{strategy_id}", summary="更新策略配置")
async def update_strategy(
    strategy_id: int = Path(..., description="策略配置 ID"),
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新策略配置
    
    - **strategy_id**: 策略配置 ID
    - **data**: 更新的数据
    """
    try:
        service = StrategyService(db)
        strategy = service.update_strategy(strategy_id, data)
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy not found: ID={strategy_id}")
        
        logger.info(f"✓ 更新策略配置: {strategy.name} (ID: {strategy.id})")
        return {
            "code": 200,
            "message": "success",
            "data": strategy.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}", summary="删除策略配置")
async def delete_strategy(
    strategy_id: int = Path(..., description="策略配置 ID"),
    db: Session = Depends(get_db)
):
    """
    删除策略配置
    
    - **strategy_id**: 策略配置 ID
    """
    try:
        service = StrategyService(db)
        success = service.delete_strategy(strategy_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Strategy not found: ID={strategy_id}")
        
        logger.info(f"✓ 删除策略配置: ID={strategy_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"deleted": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/default-parameters", summary="获取策略默认参数")
async def get_default_parameters(
    strategy_type: str = Query(..., description="策略类型（MAStrategy, MACDStrategy, RSIStrategy）")
):
    """
    获取策略默认参数（用于前端表单）
    
    - **strategy_type**: 策略类型
    """
    try:
        # 动态导入策略类
        if strategy_type == "MAStrategy":
            from app.strategies.technical.ma_cross import MAStrategy
            strategy_class = MAStrategy
        elif strategy_type == "MACDStrategy":
            from app.strategies.technical.macd_signal import MACDStrategy
            strategy_class = MACDStrategy
        elif strategy_type == "RSIStrategy":
            from app.strategies.technical.rsi_strategy import RSIStrategy
            strategy_class = RSIStrategy
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy type: {strategy_type}")
        
        # 获取默认参数
        default_params = strategy_class.get_default_parameters()
        
        logger.info(f"✓ 获取策略默认参数: {strategy_type}")
        return {
            "code": 200,
            "message": "success",
            "data": default_params
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略默认参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
