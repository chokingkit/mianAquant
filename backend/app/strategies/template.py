"""
策略模板（供用户自定义策略）
用户可基于此模板实现自己的策略
"""
from typing import Dict, Any, Optional
from datetime import date
import pandas as pd
from loguru import logger

from app.strategies.base import BaseStrategy


class CustomStrategyTemplate(BaseStrategy):
    """
    自定义策略模板
    
    使用方法：
    1. 继承 BaseStrategy
    2. 实现 initialize() 和 handle_data() 方法
    3. 在 initialize() 中设置策略参数
    4. 在 handle_data() 中实现交易逻辑
    
    Example:
        # 创建策略实例
        strategy = CustomStrategyTemplate({"param1": 10, "param2": 20})
        
        # 在回测引擎中运行
        engine = BacktestEngine()
        result = engine.run_backtest(strategy, start_date, end_date, stock_pool)
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            parameters: 策略参数字典（可在前端表单中设置）
        """
        # 设置默认参数
        default_params = {
            "param1": 10,      # 示例参数1
            "param2": 20,      # 示例参数2
            "stock_pool": [],   # 股票池
        }
        
        # 用用户参数覆盖默认参数
        if parameters:
            default_params.update(parameters)
        
        super().__init__("CustomStrategyTemplate", default_params)
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        初始化策略（在回测开始前调用一次）
        
        用于：
        - 计算长期指标（需要足够历史数据）
        - 预加载数据
        - 初始化策略状态
        
        Args:
            context: 上下文字典
        """
        self.context = context
        self.data_provider = context.get("data_provider")
        
        self.logger.info("自定义策略初始化完成")
        self.logger.info(f"策略参数: {self.parameters}")
        
        # TODO: 添加初始化逻辑
        # 例如：预加载历史数据
        # self.historical_data = {}
        # for stock_code in self.parameters["stock_pool"]:
        #     df = self.data_provider.get_stock_daily(
        #         stock_code, 
        #         context["start_date"] - pd.Timedelta(days=60), 
        #         context["start_date"]
        #     )
        #     self.historical_data[stock_code] = df
    
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
        current_date = context["current_date"]
        portfolio = context["portfolio"]
        signals = context.get("signals", {})
        
        self.logger.debug(f"处理交易日: {current_date}")
        
        # TODO: 实现交易逻辑
        # 示例：遍历股票池，根据条件生成交易信号
        # for stock_code in self.parameters["stock_pool"]:
        #     # 获取股票数据
        #     stock_data = self._get_stock_data(stock_code, current_date)
        #     
        #     # 计算技术指标
        #     if len(stock_data) >= self.parameters["param1"]:
        #         ma = stock_data['close'].tail(self.parameters["param1"]).mean()
        #         
        #         # 生成交易信号
        #         if stock_data['close'].iloc[-1] > ma:
        #             if stock_code not in portfolio.positions or portfolio.positions[stock_code] == 0:
        #                 signals[stock_code] = {"action": "buy", "quantity": 100}
        #         elif stock_code in portfolio.positions and portfolio.positions[stock_code] > 0:
        #             signals[stock_code] = {"action": "sell", "quantity": portfolio.positions[stock_code]}
        
        # 更新上下文中的 signals
        context["signals"] = signals
    
    def _get_stock_data(self, stock_code: str, current_date: date, days: int = 60) -> pd.DataFrame:
        """
        获取股票数据（历史 + 当前）
        
        Args:
            stock_code: 股票代码
            current_date: 当前日期
            days: 获取历史数据的天数
            
        Returns:
            DataFrame: 股票数据
        """
        # 从 data_provider 获取历史数据
        start_date = current_date - pd.Timedelta(days=days)
        df = self.data_provider.get_stock_daily(stock_code, start_date, current_date)
        return df
    
    def generate_signals(self, context: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号（可选重写）
        
        如果策略需要返回结构化的交易信号，可重写此方法。
        
        Args:
            context: 上下文字典
            data: 当前交易日的市场数据
            
        Returns:
            Dict: 交易信号字典
        """
        # 调用 handle_data 生成信号
        self.handle_data(context, data)
        return context.get("signals", {})
    
    def validate_parameters(self) -> bool:
        """
        验证策略参数是否合法
        
        Returns:
            bool: 参数是否合法
        """
        # TODO: 添加参数验证逻辑
        if self.parameters.get("param1", 0) <= 0:
            self.logger.error("param1 必须大于 0")
            return False
        
        return True
    
    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        返回默认参数（用于前端表单）
        
        Returns:
            Dict: 默认参数字典
        """
        return {
            "param1": 10,
            "param2": 20,
            "stock_pool": ["sh.600000", "sz.000001"],
            "description": "自定义策略模板，请修改参数和逻辑"
        }


# 使用示例
if __name__ == "__main__":
    # 创建策略实例
    strategy = CustomStrategyTemplate({
        "param1": 10,
        "param2": 20,
        "stock_pool": ["sh.600000", "sz.000001"]
    })
    
    # 验证参数
    if not strategy.validate_parameters():
        print("策略参数不合法")
        exit(1)
    
    # 初始化策略
    context = {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "current_date": None,
        "portfolio": None,
        "data_provider": None,
        "signals": {}
    }
    strategy.initialize(context)
    
    print(f"策略名称: {strategy.name}")
    print(f"策略参数: {strategy.parameters}")
    print("策略初始化成功")
