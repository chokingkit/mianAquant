"""
风险管理服务层
提供风险规则管理、风险检查、告警管理等业务逻辑
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from app.models.risk import RiskRule, RiskAlert
from app.risk.rules import create_rule, get_rule_types, RULE_TYPE_MAP
from app.risk.engine import RiskEngine
from app.risk.metrics import RiskMetrics


class RiskService:
    """
    风险管理服务
    
    提供风险规则管理、风险检查、告警管理等服务
    """
    
    def __init__(self, db: Session):
        """
        初始化风险管理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.engine = RiskEngine()
        self._load_rules_from_db()
        logger.info("✓ 风险管理服务初始化完成")
    
    def _load_rules_from_db(self) -> None:
        """从数据库加载启用的规则"""
        rules = self.db.query(RiskRule).filter(RiskRule.enabled == True).all()
        
        rule_instances = []
        for rule_model in rules:
            try:
                rule_instance = create_rule(
                    rule_type=rule_model.rule_type,
                    name=rule_model.name,
                    parameters=rule_model.parameters or {},
                    rule_id=rule_model.id
                )
                rule_instance.enabled = rule_model.enabled
                rule_instance.priority = rule_model.priority
                rule_instances.append(rule_instance)
            except ValueError as e:
                logger.error(f"加载规则失败: {rule_model.name}, 错误: {e}")
        
        self.engine.load_rules(rule_instances)
    
    # ==================== 规则管理 ====================
    
    def create_rule(self, rule_data: Dict[str, Any]) -> RiskRule:
        """
        创建风险规则
        
        Args:
            rule_data: 规则数据
                - name: 规则名称
                - rule_type: 规则类型
                - parameters: 规则参数
                - enabled: 是否启用
                - priority: 优先级
                - description: 描述
                
        Returns:
            RiskRule: 创建的记录
        """
        rule = RiskRule.from_dict(rule_data)
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        # 重新加载规则
        self._load_rules_from_db()
        
        logger.info(f"✓ 创建风险规则: ID={rule.id}, 名称={rule.name}")
        return rule
    
    def get_rule(self, rule_id: int) -> Optional[RiskRule]:
        """
        获取单个规则
        
        Args:
            rule_id: 规则 ID
            
        Returns:
            Optional[RiskRule]: 规则记录或 None
        """
        return self.db.query(RiskRule).filter(RiskRule.id == rule_id).first()
    
    def list_rules(self, rule_type: Optional[str] = None, enabled: Optional[bool] = None) -> List[RiskRule]:
        """
        列出风险规则
        
        Args:
            rule_type: 可选，按规则类型过滤
            enabled: 可选，按是否启用过滤
            
        Returns:
            List[RiskRule]: 规则列表
        """
        query = self.db.query(RiskRule)
        
        if rule_type:
            query = query.filter(RiskRule.rule_type == rule_type)
        
        if enabled is not None:
            query = query.filter(RiskRule.enabled == enabled)
        
        return query.order_by(RiskRule.priority.asc()).all()
    
    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Optional[RiskRule]:
        """
        更新风险规则
        
        Args:
            rule_id: 规则 ID
            rule_data: 更新的数据
            
        Returns:
            Optional[RiskRule]: 更新后的记录或 None
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        # 更新字段
        if 'name' in rule_data:
            rule.name = rule_data['name']
        if 'rule_type' in rule_data:
            rule.rule_type = rule_data['rule_type']
        if 'parameters' in rule_data:
            rule.parameters = rule_data['parameters']
        if 'enabled' in rule_data:
            rule.enabled = rule_data['enabled']
        if 'priority' in rule_data:
            rule.priority = rule_data['priority']
        if 'description' in rule_data:
            rule.description = rule_data['description']
        
        self.db.commit()
        self.db.refresh(rule)
        
        # 重新加载规则
        self._load_rules_from_db()
        
        logger.info(f"✓ 更新风险规则: ID={rule.id}")
        return rule
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除风险规则
        
        Args:
            rule_id: 规则 ID
            
        Returns:
            bool: 是否成功删除
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        self.db.delete(rule)
        self.db.commit()
        
        # 重新加载规则
        self._load_rules_from_db()
        
        logger.info(f"✓ 删除风险规则: ID={rule_id}")
        return True
    
    def enable_rule(self, rule_id: int, enabled: bool = True) -> bool:
        """
        启用/禁用规则
        
        Args:
            rule_id: 规则 ID
            enabled: 是否启用
            
        Returns:
            bool: 是否成功
        """
        return self.update_rule(rule_id, {'enabled': enabled}) is not None
    
    # ==================== 风险检查 ====================
    
    def check_risk(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行风险检查
        
        Args:
            context: 风险检查上下文
                - portfolio: 组合信息
                - positions: 持仓明细
                - market_data: 市场数据
                
        Returns:
            List[Dict]: 触发的告警列表
        """
        alerts = self.engine.check_risk(context)
        
        # 保存告警到数据库
        for alert in alerts:
            self._save_alert(alert)
        
        return alerts
    
    def _save_alert(self, alert_data: Dict[str, Any]) -> RiskAlert:
        """
        保存告警到数据库
        
        Args:
            alert_data: 告警数据
            
        Returns:
            RiskAlert: 保存的告警记录
        """
        alert = RiskAlert(
            rule_id=alert_data.get('rule_id'),
            rule_name=alert_data.get('rule_name', ''),
            rule_type=alert_data.get('rule_type', ''),
            alert_level=alert_data.get('alert_level', 'warning'),
            message=alert_data.get('message', ''),
            details=alert_data.get('details'),
            stock_code=alert_data.get('stock_code'),
            strategy_id=alert_data.get('strategy_id'),
            backtest_id=alert_data.get('backtest_id'),
        )
        
        self.db.add(alert)
        self.db.commit()
        
        return alert
    
    # ==================== 告警管理 ====================
    
    def get_alert(self, alert_id: int) -> Optional[RiskAlert]:
        """
        获取单个告警
        
        Args:
            alert_id: 告警 ID
            
        Returns:
            Optional[RiskAlert]: 告警记录或 None
        """
        return self.db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    
    def list_alerts(
        self,
        rule_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        is_acknowledged: Optional[bool] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[RiskAlert]:
        """
        列出告警
        
        Args:
            rule_type: 可选，按规则类型过滤
            alert_level: 可选，按告警级别过滤
            is_acknowledged: 可选，按是否已确认过滤
            is_resolved: 可选，按是否已解决过滤
            limit: 返回数量限制
            
        Returns:
            List[RiskAlert]: 告警列表
        """
        query = self.db.query(RiskAlert)
        
        if rule_type:
            query = query.filter(RiskAlert.rule_type == rule_type)
        if alert_level:
            query = query.filter(RiskAlert.alert_level == alert_level)
        if is_acknowledged is not None:
            query = query.filter(RiskAlert.is_acknowledged == is_acknowledged)
        if is_resolved is not None:
            query = query.filter(RiskAlert.is_resolved == is_resolved)
        
        return query.order_by(RiskAlert.created_at.desc()).limit(limit).all()
    
    def acknowledge_alert(self, alert_id: int) -> Optional[RiskAlert]:
        """
        确认告警
        
        Args:
            alert_id: 告警 ID
            
        Returns:
            Optional[RiskAlert]: 更新后的告警或 None
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        alert.is_acknowledged = True
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"✓ 确认告警: ID={alert_id}")
        return alert
    
    def resolve_alert(self, alert_id: int, note: Optional[str] = None) -> Optional[RiskAlert]:
        """
        解决告警
        
        Args:
            alert_id: 告警 ID
            note: 解决备注
            
        Returns:
            Optional[RiskAlert]: 更新后的告警或 None
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        if note:
            alert.resolution_note = note
        
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"✓ 解决告警: ID={alert_id}")
        return alert
    
    def delete_alert(self, alert_id: int) -> bool:
        """
        删除告警
        
        Args:
            alert_id: 告警 ID
            
        Returns:
            bool: 是否成功删除
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        self.db.delete(alert)
        self.db.commit()
        
        logger.info(f"✓ 删除告警: ID={alert_id}")
        return True
    
    # ==================== 风险指标 ====================
    
    def calculate_risk_metrics(
        self,
        equity_curve: List[float],
        returns: List[float],
        trades: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        计算风险指标
        
        Args:
            equity_curve: 权益曲线
            returns: 收益率序列
            trades: 交易记录（可选）
            
        Returns:
            Dict: 风险指标
        """
        return RiskMetrics.calculate_all_metrics(equity_curve, returns, trades)
    
    def get_rule_types(self) -> List[str]:
        """
        获取支持的规则类型
        
        Returns:
            List[str]: 规则类型列表
        """
        return get_rule_types()
    
    def get_engine_summary(self) -> Dict[str, Any]:
        """
        获取风险引擎汇总信息
        
        Returns:
            Dict: 汇总信息
        """
        return self.engine.get_rule_summary()
