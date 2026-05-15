"""
风险管理 API 端点
提供风险规则管理、风险检查、告警管理的 REST API
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from loguru import logger

from app.models.risk import RiskRule, RiskAlert
from app.services.risk_service import RiskService
from app.api.deps import get_db

router = APIRouter()


# ==================== 规则管理 ====================


@router.post("/rules", summary="创建风险规则")
async def create_risk_rule(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建风险规则
    
    Request Body:
        {
            "name": "止损规则",
            "rule_type": "stop_loss",
            "parameters": {"stop_loss_ratio": 0.05},
            "enabled": true,
            "priority": 100,
            "description": "5% 止损"
        }
        
    rule_type 可选值：
        - position_limit: 仓位限制
        - stop_loss: 止损
        - take_profit: 止盈
    """
    try:
        # 验证必填字段
        required_fields = ['name', 'rule_type', 'parameters']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
        
        # 验证 rule_type
        from app.risk.rules import RULE_TYPE_MAP
        if data['rule_type'] not in RULE_TYPE_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"无效的 rule_type: {data['rule_type']}，可选值: {list(RULE_TYPE_MAP.keys())}"
            )
        
        service = RiskService(db)
        rule = service.create_rule(data)
        
        logger.info(f"✓ 创建风险规则: ID={rule.id}, 名称={rule.name}")
        return {
            "code": 200,
            "message": "success",
            "data": rule.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建风险规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", summary="列出风险规则")
async def list_risk_rules(
    rule_type: Optional[str] = Query(None, description="规则类型过滤"),
    enabled: Optional[bool] = Query(None, description="是否启用过滤"),
    db: Session = Depends(get_db)
):
    """
    列出风险规则（支持过滤）
    
    - **rule_type**: 可选，过滤规则类型
    - **enabled**: 可选，过滤是否启用
    """
    try:
        service = RiskService(db)
        rules = service.list_rules(rule_type=rule_type, enabled=enabled)
        
        result_list = [r.to_dict() for r in rules]
        
        logger.info(f"✓ 列出风险规则: {len(result_list)} 个")
        return {
            "code": 200,
            "message": "success",
            "data": result_list
        }
    except Exception as e:
        logger.error(f"列出风险规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/types", summary="获取规则类型")
async def get_rule_types():
    """
    获取支持的规则类型
    """
    try:
        from app.risk.rules import get_rule_types
        
        types = get_rule_types()
        
        logger.info(f"✓ 获取规则类型: {types}")
        return {
            "code": 200,
            "message": "success",
            "data": {
                "types": types,
                "descriptions": {
                    "position_limit": "仓位限制规则",
                    "stop_loss": "止损规则",
                    "take_profit": "止盈规则"
                }
            }
        }
    except Exception as e:
        logger.error(f"获取规则类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", summary="获取风险规则")
async def get_risk_rule(
    rule_id: int = Path(..., description="规则 ID"),
    db: Session = Depends(get_db)
):
    """
    获取单个风险规则
    
    - **rule_id**: 规则 ID
    """
    try:
        service = RiskService(db)
        rule = service.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Risk rule not found: ID={rule_id}")
        
        logger.info(f"✓ 获取风险规则: ID={rule.id}")
        return {
            "code": 200,
            "message": "success",
            "data": rule.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", summary="更新风险规则")
async def update_risk_rule(
    rule_id: int = Path(..., description="规则 ID"),
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新风险规则
    
    - **rule_id**: 规则 ID
    """
    try:
        service = RiskService(db)
        rule = service.update_rule(rule_id, data)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Risk rule not found: ID={rule_id}")
        
        logger.info(f"✓ 更新风险规则: ID={rule.id}")
        return {
            "code": 200,
            "message": "success",
            "data": rule.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新风险规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", summary="删除风险规则")
async def delete_risk_rule(
    rule_id: int = Path(..., description="规则 ID"),
    db: Session = Depends(get_db)
):
    """
    删除风险规则
    
    - **rule_id**: 规则 ID
    """
    try:
        service = RiskService(db)
        success = service.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Risk rule not found: ID={rule_id}")
        
        logger.info(f"✓ 删除风险规则: ID={rule_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"deleted": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除风险规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/enable", summary="启用/禁用规则")
async def enable_risk_rule(
    rule_id: int = Path(..., description="规则 ID"),
    enabled: bool = Query(..., description="是否启用"),
    db: Session = Depends(get_db)
):
    """
    启用/禁用规则
    
    - **rule_id**: 规则 ID
    - **enabled**: 是否启用（query 参数）
    """
    try:
        service = RiskService(db)
        success = service.enable_rule(rule_id, enabled)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Risk rule not found: ID={rule_id}")
        
        status = "启用" if enabled else "禁用"
        logger.info(f"✓ {status}规则: ID={rule_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"enabled": enabled}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用/禁用规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 风险检查 ====================


@router.post("/check", summary="执行风险检查")
async def check_risk(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    执行风险检查
    
    Request Body:
        {
            "portfolio": {"total_value": 100000, "cash": 50000},
            "positions": {
                "sh.600000": {"value": 20000, "cost_price": 10.5, "quantity": 1000}
            },
            "market_data": {
                "sh.600000": {"close": 10.0}
            },
            "strategy_id": 1,
            "backtest_id": 1
        }
    """
    try:
        service = RiskService(db)
        alerts = service.check_risk(data)
        
        logger.info(f"✓ 风险检查完成: {len(alerts)} 个告警")
        return {
            "code": 200,
            "message": "success",
            "data": {
                "alert_count": len(alerts),
                "alerts": alerts
            }
        }
    except Exception as e:
        logger.error(f"风险检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 告警管理 ====================


@router.get("/alerts", summary="列出告警")
async def list_alerts(
    rule_type: Optional[str] = Query(None, description="规则类型过滤"),
    alert_level: Optional[str] = Query(None, description="告警级别过滤（info/warning/critical）"),
    is_acknowledged: Optional[bool] = Query(None, description="是否已确认过滤"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决过滤"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    列出告警（支持过滤）
    
    - **rule_type**: 可选，过滤规则类型
    - **alert_level**: 可选，过滤告警级别
    - **is_acknowledged**: 可选，过滤是否已确认
    - **is_resolved**: 可选，过滤是否已解决
    - **limit**: 返回数量限制
    """
    try:
        service = RiskService(db)
        alerts = service.list_alerts(
            rule_type=rule_type,
            alert_level=alert_level,
            is_acknowledged=is_acknowledged,
            is_resolved=is_resolved,
            limit=limit
        )
        
        result_list = [a.to_dict() for a in alerts]
        
        logger.info(f"✓ 列出告警: {len(result_list)} 个")
        return {
            "code": 200,
            "message": "success",
            "data": result_list
        }
    except Exception as e:
        logger.error(f"列出告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge", summary="确认告警")
async def acknowledge_alert(
    alert_id: int = Path(..., description="告警 ID"),
    db: Session = Depends(get_db)
):
    """
    确认告警
    
    - **alert_id**: 告警 ID
    """
    try:
        service = RiskService(db)
        alert = service.acknowledge_alert(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Risk alert not found: ID={alert_id}")
        
        logger.info(f"✓ 确认告警: ID={alert_id}")
        return {
            "code": 200,
            "message": "success",
            "data": alert.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", summary="解决告警")
async def resolve_alert(
    alert_id: int = Path(..., description="告警 ID"),
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    解决告警
    
    - **alert_id**: 告警 ID
    
    Request Body:
        {"note": "已处理"}
    """
    try:
        note = data.get('note')
        
        service = RiskService(db)
        alert = service.resolve_alert(alert_id, note)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Risk alert not found: ID={alert_id}")
        
        logger.info(f"✓ 解决告警: ID={alert_id}")
        return {
            "code": 200,
            "message": "success",
            "data": alert.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/{alert_id}", summary="删除告警")
async def delete_alert(
    alert_id: int = Path(..., description="告警 ID"),
    db: Session = Depends(get_db)
):
    """
    删除告警
    
    - **alert_id**: 告警 ID
    """
    try:
        service = RiskService(db)
        success = service.delete_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Risk alert not found: ID={alert_id}")
        
        logger.info(f"✓ 删除告警: ID={alert_id}")
        return {
            "code": 200,
            "message": "success",
            "data": {"deleted": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 风险指标 ====================


@router.post("/metrics", summary="计算风险指标")
async def calculate_risk_metrics(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    计算风险指标（最大回撤、夏普比率、VaR 等）
    
    Request Body:
        {
            "equity_curve": [100000, 101000, 99000, ...],
            "returns": [0.01, -0.02, 0.015, ...],
            "trades": [...]  # 可选
        }
    """
    try:
        equity_curve = data.get('equity_curve', [])
        returns = data.get('returns', [])
        trades = data.get('trades')
        
        if not equity_curve or not returns:
            raise HTTPException(status_code=400, detail="equity_curve 和 returns 为必填字段")
        
        service = RiskService(db)
        metrics = service.calculate_risk_metrics(equity_curve, returns, trades)
        
        logger.info(f"✓ 风险指标计算完成")
        return {
            "code": 200,
            "message": "success",
            "data": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算风险指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", summary="获取风险汇总")
async def get_risk_summary(db: Session = Depends(get_db)):
    """
    获取风险汇总信息（规则数量、告警数量等）
    """
    try:
        service = RiskService(db)
        summary = service.get_engine_summary()
        
        logger.info(f"✓ 获取风险汇总")
        return {
            "code": 200,
            "message": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"获取风险汇总失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
