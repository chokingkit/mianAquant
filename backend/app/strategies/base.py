"""
策略基类（所有策略必须继承此类）
定义策略的生命周期方法：initialize, handle_data, generate_signals
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
from loguru import logger


class BaseStrategy(ABC):
    """
    策略基类（抽象类）
    
    所有策略必须继承此类并实现以下方法：
    - initialize(): 初始化策略（在回测开始前调用一次）
    - handle_data(): 处理每个交易日的数据（核心逻辑）
    
    可选重写：
    - generate_signals(): 生成交易信号（结构化输出）
    - validate_parameters(): 验证策略参数
    - get_default_parameters(): 返回默认参数（用于前端表单）
    """
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            parameters: 策略参数字典
        """
        self.name = name
        self.parameters = parameters or {}
        self.context = None
        self.logger = logger.bind(strategy=name)
        self.logger.info(f"策略初始化: {name}, 参数: {self.parameters}")
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        初始化策略（在回测开始前调用一次）
        
        用于：
        - 计算长期指标（需要足够历史数据）
        - 预加载数据
        - 初始化策略状态
        
        Args:
            context: 上下文字典，包含：
                - start_date: 回测开始日期
                - end_date: 回测结束日期
                - portfolio: 投资组合对象
                - data_provider: 数据提供者
        """
        pass
    
    @abstractmethod
    def handle_data(self, context: Dict[str, Any], data: pd.DataFrame) -> None:
        """
        处理每个交易日的数据（核心逻辑）
        
        在每个交易日调用，策略的核心逻辑应在此实现：
        - 计算技术指标
        - 生成交易信号
        - 更新上下文中的 signals
        
        Args:
            context: 上下文字典，包含：
                - current_date: 当前交易日
                - portfolio: 投资组合对象
                - signals: 交易信号字典（策略应更新此字典）
                - data_provider: 数据提供者
            data: 当前交易日的市场数据（多只股票）
                  列：code, name, open, high, low, close, volume, amount, ...
        """
        pass
    
    def generate_signals(self, context: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号（可选重写）
        
        如果策略需要返回结构化的交易信号，可重写此方法。
        
        Args:
            context: 上下文字典
            data: 当前交易日的市场数据
            
        Returns:
            Dict: 交易信号字典，格式：
                {
                    "sh.600000": {"action": "buy", "quantity": 100, "price": 10.5},
                    "sz.000001": {"action": "sell", "quantity": 200}
                }
        """
        return {}
    
    def validate_parameters(self) -> bool:
        """
        验证策略参数是否合法
        
        Returns:
            bool: 参数是否合法
        """
        return True
    
    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        返回默认参数（用于前端表单）
        
        Returns:
            Dict: 默认参数字典
        """
        return {}
    
    def calculate_indicators(self, stock_code: str, data: pd.DataFrame) -> Dict[str, float]:
        """
        计算技术指标（辅助方法）
        
        Args:
            stock_code: 股票代码
            data: 历史数据 DataFrame
            
        Returns:
            Dict: 技术指标字典
        """
        if data.empty or 'close' not in data.columns:
            return {}
        
        indicators = {}
        
        # 计算 MA
        for window in [5, 10, 20, 60]:
            if len(data) >= window:
                indicators[f'MA{window}'] = data['close'].tail(window).mean()
        
        # 计算 RSI
        if len(data) >= 14:
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            indicators['RSI'] = 100 - (100 / (1 + rs.iloc[-1]))
        
        return indicators
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, params={self.parameters})>"
