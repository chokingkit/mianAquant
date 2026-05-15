"""
策略服务（CRUD 操作）
提供策略配置的增删改查功能
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.models.strategy import StrategyConfig


class StrategyService:
    """
    策略服务
    
    提供策略配置的 CRUD 操作：
    - create_strategy(): 创建策略配置
    - get_strategy(): 获取策略配置
    - list_strategies(): 列出所有策略
    - update_strategy(): 更新策略配置
    - delete_strategy(): 删除策略配置
    """
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.logger = logger.bind(module="StrategyService")
        self.logger.info("✓ 策略服务初始化完成")
    
    def create_strategy(self, data: Dict[str, Any]) -> StrategyConfig:
        """
        创建策略配置
        
        Args:
            data: 策略配置数据
                {
                    "name": "My MA Strategy",
                    "strategy_type": "MAStrategy",
                    "parameters": {...},
                    "stock_pool": [...],
                    "description": "...",
                    "is_active": true
                }
                
        Returns:
            StrategyConfig: 创建的策略配置实例
        """
        # 创建实例
        strategy = StrategyConfig(
            name=data.get("name"),
            strategy_type=data.get("strategy_type"),
            parameters=data.get("parameters"),
            stock_pool=data.get("stock_pool"),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            created_by=data.get("created_by")
        )
        
        # 保存到数据库
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        
        self.logger.info(f"✓ 创建策略配置: {strategy.name} (ID: {strategy.id})")
        return strategy
    
    def get_strategy(self, strategy_id: int) -> Optional[StrategyConfig]:
        """
        获取策略配置
        
        Args:
            strategy_id: 策略配置 ID
            
        Returns:
            StrategyConfig: 策略配置实例（None 表示未找到）
        """
        return self.db.query(StrategyConfig).filter(StrategyConfig.id == strategy_id).first()
    
    def list_strategies(self, 
                        strategy_type: Optional[str] = None, 
                        is_active: Optional[bool] = None) -> List[StrategyConfig]:
        """
        列出策略配置
        
        Args:
            strategy_type: 策略类型（可选，用于过滤）
            is_active: 是否激活（可选，用于过滤）
            
        Returns:
            List[StrategyConfig]: 策略配置列表
        """
        query = self.db.query(StrategyConfig)
        
        # 过滤策略类型
        if strategy_type:
            query = query.filter(StrategyConfig.strategy_type == strategy_type)
        
        # 过滤激活状态
        if is_active is not None:
            query = query.filter(StrategyConfig.is_active == is_active)
        
        # 按创建时间降序排列
        query = query.order_by(StrategyConfig.created_at.desc())
        
        return query.all()
    
    def update_strategy(self, 
                        strategy_id: int, 
                        data: Dict[str, Any]) -> Optional[StrategyConfig]:
        """
        更新策略配置
        
        Args:
            strategy_id: 策略配置 ID
            data: 更新的数据
            
        Returns:
            StrategyConfig: 更新后的策略配置实例（None 表示未找到）
        """
        strategy = self.get_strategy(strategy_id)
        
        if not strategy:
            self.logger.warning(f"策略配置未找到: ID={strategy_id}")
            return None
        
        # 更新字段
        if "name" in data:
            strategy.name = data["name"]
        
        if "strategy_type" in data:
            strategy.strategy_type = data["strategy_type"]
        
        if "parameters" in data:
            strategy.parameters = data["parameters"]
        
        if "stock_pool" in data:
            strategy.stock_pool = data["stock_pool"]
        
        if "description" in data:
            strategy.description = data["description"]
        
        if "is_active" in data:
            strategy.is_active = data["is_active"]
        
        # 保存到数据库
        self.db.commit()
        self.db.refresh(strategy)
        
        self.logger.info(f"✓ 更新策略配置: {strategy.name} (ID: {strategy.id})")
        return strategy
    
    def delete_strategy(self, strategy_id: int) -> bool:
        """
        删除策略配置
        
        Args:
            strategy_id: 策略配置 ID
            
        Returns:
            bool: 是否删除成功
        """
        strategy = self.get_strategy(strategy_id)
        
        if not strategy:
            self.logger.warning(f"策略配置未找到: ID={strategy_id}")
            return False
        
        # 删除
        self.db.delete(strategy)
        self.db.commit()
        
        self.logger.info(f"✓ 删除策略配置: {strategy.name} (ID: {strategy.id})")
        return True
    
    def create_strategy_instance(self, strategy_id: int) -> Optional[Any]:
        """
        根据策略配置创建策略实例
        
        Args:
            strategy_id: 策略配置 ID
            
        Returns:
            策略实例（BaseStrategy 子类），None 表示创建失败
        """
        strategy = self.get_strategy(strategy_id)
        
        if not strategy:
            self.logger.warning(f"策略配置未找到: ID={strategy_id}")
            return None
        
        # 创建策略实例
        return strategy.create_strategy_instance()
