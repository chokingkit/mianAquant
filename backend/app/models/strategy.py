"""
策略配置模型（SQLAlchemy ORM）
定义 StrategyConfig 表结构
"""
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.sql import func
from loguru import logger

from app.models.base import Base


class StrategyConfig(Base):
    """
    策略配置表
    
    存储用户的策略配置（参数、股票池等）
    """
    __tablename__ = 'strategy_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='策略名称')
    strategy_type = Column(String(50), nullable=False, index=True, comment='策略类型（MAStrategy, MACDStrategy, etc.）')
    parameters = Column(JSON, comment='策略参数（JSON 格式）')
    stock_pool = Column(JSON, comment='股票池（JSON 数组）')
    description = Column(Text, comment='策略描述')
    is_active = Column(Boolean, default=True, index=True, comment='是否激活')
    created_by = Column(String(50), comment='创建者')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_type_active', 'strategy_type', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<StrategyConfig(id={self.id}, name={self.name}, type={self.strategy_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'strategy_type': self.strategy_type,
            'parameters': self.parameters,
            'stock_pool': self.stock_pool,
            'description': self.description,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """
        从字典创建实例
        
        Args:
            data: 参数字典
            
        Returns:
            StrategyConfig: 实例
        """
        return cls(
            name=data.get('name'),
            strategy_type=data.get('strategy_type'),
            parameters=data.get('parameters'),
            stock_pool=data.get('stock_pool'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by')
        )
    
    def create_strategy_instance(self) -> Optional[Any]:
        """
        根据配置创建策略实例
        
        Returns:
            策略实例（BaseStrategy 子类），None 表示创建失败
        """
        try:
            # 动态导入策略类
            if self.strategy_type == 'MAStrategy':
                from app.strategies.technical.ma_cross import MAStrategy
                strategy_class = MAStrategy
            elif self.strategy_type == 'MACDStrategy':
                from app.strategies.technical.macd_signal import MACDStrategy
                strategy_class = MACDStrategy
            elif self.strategy_type == 'RSIStrategy':
                from app.strategies.technical.rsi_strategy import RSIStrategy
                strategy_class = RSIStrategy
            else:
                logger.error(f"未知策略类型: {self.strategy_type}")
                return None
            
            # 创建策略实例
            parameters = self.parameters or {}
            instance = strategy_class(parameters=parameters)
            
            logger.info(f"✓ 创建策略实例: {self.name} ({self.strategy_type})")
            return instance
            
        except Exception as e:
            logger.error(f"创建策略实例失败: {e}")
            return None
