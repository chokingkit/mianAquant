"""
风险规则引擎
负责加载、管理和执行风险规则
"""
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger

from app.risk.rules import BaseRiskRule, PositionLimitRule, StopLossRule, TakeProfitRule, create_rule, get_rule_types


class RiskEngine:
    """
    风险规则引擎
    
    负责加载、管理和执行风险规则
    """
    
    def __init__(self):
        """初始化风险引擎"""
        self.rules: List[BaseRiskRule] = []
        self.alerts: List[Dict[str, Any]] = []
        logger.info("✓ 风险引擎初始化完成")
    
    def load_rules(self, rules: List[BaseRiskRule]) -> None:
        """
        加载风险规则列表
        
        Args:
            rules: 风险规则列表
        """
        self.rules = sorted(rules, key=lambda r: r.priority)
        logger.info(f"✓ 加载 {len(self.rules)} 条风险规则")
    
    def add_rule(self, rule: BaseRiskRule) -> None:
        """
        添加单条风险规则
        
        Args:
            rule: 风险规则
        """
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
        logger.info(f"✓ 添加风险规则: {rule.name} (优先级: {rule.priority})")
    
    def remove_rule(self, rule_id: int) -> bool:
        """
        移除风险规则
        
        Args:
            rule_id: 规则 ID
            
        Returns:
            bool: 是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                removed = self.rules.pop(i)
                logger.info(f"✓ 移除风险规则: {removed.name}")
                return True
        
        logger.warning(f"⚠ 未找到规则 ID: {rule_id}")
        return False
    
    def enable_rule(self, rule_id: int, enabled: bool = True) -> bool:
        """
        启用/禁用规则
        
        Args:
            rule_id: 规则 ID
            enabled: 是否启用
            
        Returns:
            bool: 是否成功设置
        """
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = enabled
                status = "启用" if enabled else "禁用"
                logger.info(f"✓ {status}规则: {rule.name}")
                return True
        
        return False
    
    def check_risk(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行所有启用规则的风险检查
        
        Args:
            context: 风险检查上下文，包含：
                - portfolio: 组合信息
                - positions: 持仓明细
                - market_data: 市场数据
                - trades: 交易记录
                
        Returns:
            List[Dict]: 触发的告警列表
        """
        all_alerts = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                alerts = rule.check(context)
                if alerts:
                    # 统一转换为列表
                    if isinstance(alerts, dict):
                        alerts = [alerts]
                    
                    for alert in alerts:
                        alert['rule_id'] = rule.rule_id
                        alert['rule_name'] = rule.name
                        all_alerts.append(alert)
                    
                    logger.warning(f"⚠ 规则触发: {rule.name}, 告警数: {len(alerts)}")
            except Exception as e:
                logger.error(f"规则检查失败: {rule.name}, 错误: {e}")
        
        self.alerts.extend(all_alerts)
        return all_alerts
    
    def get_alerts(self, level: Optional[str] = None, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        获取告警列表
        
        Args:
            level: 可选，按告警级别过滤
            resolved: 可选，按是否已解决过滤
            
        Returns:
            List[Dict]: 告警列表
        """
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a.get('alert_level') == level]
        
        return alerts
    
    def clear_alerts(self) -> None:
        """清空告警列表"""
        self.alerts.clear()
        logger.info("✓ 告警列表已清空")
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """
        获取规则汇总信息
        
        Returns:
            Dict: 规则汇总
        """
        enabled_count = sum(1 for r in self.rules if r.enabled)
        disabled_count = len(self.rules) - enabled_count
        
        # 按类型统计
        type_counts = {}
        for rule in self.rules:
            rule_type = rule.__class__.__name__
            type_counts[rule_type] = type_counts.get(rule_type, 0) + 1
        
        return {
            'total_rules': len(self.rules),
            'enabled_count': enabled_count,
            'disabled_count': disabled_count,
            'type_counts': type_counts,
            'alert_count': len(self.alerts),
        }
    
    @classmethod
    def from_rule_configs(cls, rule_configs: List[Dict[str, Any]]) -> 'RiskEngine':
        """
        从规则配置列表创建引擎
        
        Args:
            rule_configs: 规则配置列表，每个配置包含：
                - rule_type: 规则类型
                - name: 规则名称
                - parameters: 规则参数
                - enabled: 是否启用
                - priority: 优先级
                
        Returns:
            RiskEngine: 风险引擎实例
        """
        engine = cls()
        
        for config in rule_configs:
            rule = create_rule(
                rule_type=config.get('rule_type'),
                name=config.get('name', '未命名规则'),
                parameters=config.get('parameters', {}),
                rule_id=config.get('id')
            )
            rule.enabled = config.get('enabled', True)
            rule.priority = config.get('priority', 100)
            engine.add_rule(rule)
        
        return engine
