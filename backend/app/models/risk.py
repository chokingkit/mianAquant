"""
风险管理模型（SQLAlchemy ORM）
定义 RiskRule 和 RiskAlert 表结构
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.sql import func
from loguru import logger

from app.models.base import Base


class RiskRule(Base):
    """
    风险规则表
    
    存储用户定义的风险控制规则（仓位限制、止损、止盈等）
    """
    __tablename__ = 'risk_rule'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    rule_type = Column(String(50), nullable=False, index=True, comment='规则类型（position_limit/stop_loss/take_profit）')
    enabled = Column(Boolean, default=True, index=True, comment='是否启用')
    priority = Column(Integer, default=100, comment='优先级（数值越小优先级越高）')
    
    # 规则参数（JSON 格式，不同规则类型有不同的参数）
    parameters = Column(JSON, comment='规则参数（JSON 格式）')
    
    # 规则描述
    description = Column(Text, comment='规则描述')
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_type_enabled', 'rule_type', 'enabled'),
    )
    
    def __repr__(self) -> str:
        return f"<RiskRule(id={self.id}, name={self.name}, type={self.rule_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'rule_type': self.rule_type,
            'enabled': self.enabled,
            'priority': self.priority,
            'parameters': self.parameters,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskRule':
        """
        从字典创建实例
        
        Args:
            data: 规则数据字典
            
        Returns:
            RiskRule: 实例
        """
        return cls(
            name=data.get('name'),
            rule_type=data.get('rule_type'),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 100),
            parameters=data.get('parameters'),
            description=data.get('description')
        )


class RiskAlert(Base):
    """
    风险告警表
    
    存储风险规则触发时产生的告警记录
    """
    __tablename__ = 'risk_alert'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, index=True, comment='触发的风险规则 ID')
    rule_name = Column(String(100), comment='规则名称')
    rule_type = Column(String(50), index=True, comment='规则类型')
    
    # 告警信息
    alert_level = Column(String(20), default='warning', index=True, comment='告警级别（info/warning/critical）')
    message = Column(Text, nullable=False, comment='告警消息')
    details = Column(JSON, comment='详细信息（JSON 格式）')
    
    # 关联的交易信息
    stock_code = Column(String(20), index=True, comment='股票代码')
    strategy_id = Column(Integer, index=True, comment='策略 ID')
    backtest_id = Column(Integer, index=True, comment='回测 ID')
    
    # 状态
    is_acknowledged = Column(Boolean, default=False, index=True, comment='是否已确认')
    is_resolved = Column(Boolean, default=False, index=True, comment='是否已解决')
    resolved_at = Column(DateTime, comment='解决时间')
    resolution_note = Column(Text, comment='解决备注')
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_rule_created', 'rule_id', 'created_at'),
        Index('idx_stock_created', 'stock_code', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<RiskAlert(id={self.id}, level={self.alert_level}, rule={self.rule_name})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'alert_level': self.alert_level,
            'message': self.message,
            'details': self.details,
            'stock_code': self.stock_code,
            'strategy_id': self.strategy_id,
            'backtest_id': self.backtest_id,
            'is_acknowledged': self.is_acknowledged,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_rule(cls, rule: RiskRule, message: str, details: Dict[str, Any]) -> 'RiskAlert':
        """
        从风险规则创建告警
        
        Args:
            rule: 触发的规则
            message: 告警消息
            details: 详细信息
            
        Returns:
            RiskAlert: 实例
        """
        return cls(
            rule_id=rule.id,
            rule_name=rule.name,
            rule_type=rule.rule_type,
            alert_level='warning',
            message=message,
            details=details
        )
