"""
均线交叉策略（短均线穿过长均线买入，反之卖出）
经典的技术分析策略
"""
from typing import Dict, Any, Optional
from datetime import date
import pandas as pd
from loguru import logger

from app.strategies.base import BaseStrategy


class MAStrategy(BaseStrategy):
    """
    均线交叉策略
    
    策略逻辑：
    - 短均线（如 5日）向上穿过长均线（如 20日）→ 买入信号
    - 短均线向下穿过长均线 → 卖出信号
    
    参数：
    - short_window: 短均线窗口（默认 5）
    - long_window: 长均线窗口（默认 20）
    - stock_pool: 股票池（list of stock codes）
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        初始化 MA 策略
        
        Args:
            parameters: 策略参数字典
                - short_window: 短均线窗口
                - long_window: 长均线窗口
                - stock_pool: 股票池
        """
        # 设置默认参数
        default_params = {
            "short_window": 5,
            "long_window": 20,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1  # 单只股票最大持仓比例
        }
        
        # 用用户参数覆盖默认参数
        if parameters:
            default_params.update(parameters)
        
        super().__init__("MAStrategy", default_params)
        
        # 验证参数
        if self.parameters["short_window"] >= self.parameters["long_window"]:
            raise ValueError("short_window 必须小于 long_window")
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        初始化策略（在回测开始前调用一次）
        
        用于计算长期指标（需要足够历史数据）
        
        Args:
            context: 上下文字典
        """
        self.context = context
        self.data_provider = context.get("data_provider")
        
        # 获取历史数据用于计算长期均线
        self.historical_data = {}
        for stock_code in self.parameters["stock_pool"]:
            try:
                df = self.data_provider.get_stock_daily(
                    stock_code, 
                    context["start_date"] - pd.Timedelta(days=60), 
                    context["start_date"]
                )
                self.historical_data[stock_code] = df
                self.logger.info(f"加载股票 {stock_code} 历史数据: {len(df)} 条")
            except Exception as e:
                self.logger.error(f"加载股票 {stock_code} 历史数据失败: {e}")
                self.historical_data[stock_code] = pd.DataFrame()
        
        self.logger.info(f"✓ MA策略初始化完成，股票池: {len(self.parameters['stock_pool'])} 只")
    
    def handle_data(self, context: Dict[str, Any], data: pd.DataFrame) -> None:
        """
        处理每个交易日的数据（核心逻辑）
        
        计算每个股票的均线，生成交易信号
        
        Args:
            context: 上下文字典
            data: 当前交易日的市场数据
        """
        current_date = context["current_date"]
        portfolio = context["portfolio"]
        signals = context.get("signals", {})
        
        self.logger.debug(f"处理交易日: {current_date}")
        
        for stock_code in self.parameters["stock_pool"]:
            # 获取股票数据（历史 + 当前）
            stock_data = self._get_stock_data(stock_code, current_date)
            
            if len(stock_data) < self.parameters["long_window"]:
                self.logger.debug(f"股票 {stock_code} 数据不足，跳过")
                continue  # 数据不足，跳过
            
            # 计算短均线和长均线
            short_ma = stock_data['close'].tail(self.parameters["short_window"]).mean()
            long_ma = stock_data['close'].tail(self.parameters["long_window"]).mean()
            
            # 计算昨天的均线（用于判断交叉）
            if len(stock_data) >= self.parameters["long_window"] + 1:
                prev_short_ma = stock_data['close'].iloc[-self.parameters["short_window"]-1:-1].mean()
                prev_long_ma = stock_data['close'].iloc[-self.parameters["long_window"]-1:-1].mean()
            else:
                prev_short_ma = short_ma
                prev_long_ma = long_ma
            
            # 生成交易信号
            current_position = portfolio.positions.get(stock_code, 0)
            
            # 黄金交叉（短均线上穿长均线）→ 买入
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                if current_position == 0:
                    # 计算买入数量（使用可用资金的一定比例）
                    available_cash = portfolio.cash
                    max_position_value = available_cash * self.parameters["max_position_pct"]
                    current_price = stock_data['close'].iloc[-1]
                    quantity = int(max_position_value / current_price / 100) * 100  # 100股的整数倍
                    
                    if quantity > 0:
                        signals[stock_code] = {
                            "action": "buy", 
                            "quantity": quantity,
                            "price": current_price,
                            "reason": f"Golden cross: short_MA={short_ma:.2f}, long_MA={long_ma:.2f}"
                        }
                        self.logger.info(f"生成买入信号: {stock_code}, 数量: {quantity}, 价格: {current_price:.2f}")
            
            # 死亡交叉（短均线下穿长均线）→ 卖出
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                if current_position > 0:
                    signals[stock_code] = {
                        "action": "sell", 
                        "quantity": current_position,
                        "price": stock_data['close'].iloc[-1],
                        "reason": f"Death cross: short_MA={short_ma:.2f}, long_MA={long_ma:.2f}"
                    }
                    self.logger.info(f"生成卖出信号: {stock_code}, 数量: {current_position}")
            
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
        # 从 historical_data 获取历史数据
        hist_df = self.historical_data.get(stock_code, pd.DataFrame())
        
        # 从 data_provider 获取当前数据
        try:
            current_df = self.data_provider.get_stock_daily(
                stock_code, 
                current_date - pd.Timedelta(days=days), 
                current_date
            )
            # 合并
            df = pd.concat([hist_df, current_df]).drop_duplicates(subset=['date']).sort_values('date')
            return df
        except Exception as e:
            self.logger.error(f"获取股票 {stock_code} 数据失败: {e}")
            return hist_df
    
    def generate_signals(self, context: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号（重写父类方法）
        
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
        if self.parameters["short_window"] <= 0:
            self.logger.error("short_window 必须大于 0")
            return False
        
        if self.parameters["long_window"] <= 0:
            self.logger.error("long_window 必须大于 0")
            return False
        
        if self.parameters["short_window"] >= self.parameters["long_window"]:
            self.logger.error("short_window 必须小于 long_window")
            return False
        
        if not self.parameters["stock_pool"]:
            self.logger.error("stock_pool 不能为空")
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
            "short_window": 5,
            "long_window": 20,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1,
            "description": "均线交叉策略：短均线上穿长均线买入，下穿卖出"
        }
