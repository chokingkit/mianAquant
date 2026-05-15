"""
RSI 策略
基于 RSI 指标生成交易信号（超买/超卖）
"""
from typing import Dict, Any, Optional
from datetime import date
import pandas as pd
from loguru import logger

from app.strategies.base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI 策略
    
    策略逻辑：
    - RSI < 30 → 超卖区域，买入信号
    - RSI > 70 → 超买区域，卖出信号
    
    参数：
    - rsi_window: RSI 计算窗口（默认 14）
    - overbought: 超买阈值（默认 70）
    - oversold: 超卖阈值（默认 30）
    - stock_pool: 股票池
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        初始化 RSI 策略
        
        Args:
            parameters: 策略参数字典
        """
        # 设置默认参数
        default_params = {
            "rsi_window": 14,
            "overbought": 70,
            "oversold": 30,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1
        }
        
        # 用用户参数覆盖默认参数
        if parameters:
            default_params.update(parameters)
        
        super().__init__("RSIStrategy", default_params)
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        初始化策略
        
        Args:
            context: 上下文字典
        """
        self.context = context
        self.data_provider = context.get("data_provider")
        
        # 获取历史数据用于计算 RSI
        self.historical_data = {}
        for stock_code in self.parameters["stock_pool"]:
            try:
                df = self.data_provider.get_stock_daily(
                    stock_code, 
                    context["start_date"] - pd.Timedelta(days=90), 
                    context["start_date"]
                )
                self.historical_data[stock_code] = df
                self.logger.info(f"加载股票 {stock_code} 历史数据: {len(df)} 条")
            except Exception as e:
                self.logger.error(f"加载股票 {stock_code} 历史数据失败: {e}")
                self.historical_data[stock_code] = pd.DataFrame()
        
        self.logger.info(f"✓ RSI 策略初始化完成，股票池: {len(self.parameters['stock_pool'])} 只")
    
    def handle_data(self, context: Dict[str, Any], data: pd.DataFrame) -> None:
        """
        处理每个交易日的数据
        
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
            
            if len(stock_data) < self.parameters["rsi_window"] + 1:
                self.logger.debug(f"股票 {stock_code} 数据不足，跳过")
                continue
            
            # 计算 RSI
            rsi = self._calculate_rsi(stock_data)
            
            if rsi is None:
                continue
            
            current_position = portfolio.positions.get(stock_code, 0)
            
            # RSI < 超卖阈值 → 买入信号
            if rsi < self.parameters["oversold"]:
                if current_position == 0:
                    # 计算买入数量
                    available_cash = portfolio.cash
                    max_position_value = available_cash * self.parameters["max_position_pct"]
                    current_price = stock_data['close'].iloc[-1]
                    quantity = int(max_position_value / current_price / 100) * 100
                    
                    if quantity > 0:
                        signals[stock_code] = {
                            "action": "buy", 
                            "quantity": quantity,
                            "price": current_price,
                            "reason": f"RSI oversold: {rsi:.2f}"
                        }
                        self.logger.info(f"生成买入信号: {stock_code}, RSI={rsi:.2f}")
            
            # RSI > 超买阈值 → 卖出信号
            elif rsi > self.parameters["overbought"]:
                if current_position > 0:
                    signals[stock_code] = {
                        "action": "sell", 
                        "quantity": current_position,
                        "price": stock_data['close'].iloc[-1],
                        "reason": f"RSI overbought: {rsi:.2f}"
                    }
                    self.logger.info(f"生成卖出信号: {stock_code}, RSI={rsi:.2f}")
            
            # 更新上下文中的 signals
            context["signals"] = signals
    
    def _get_stock_data(self, stock_code: str, current_date: date, days: int = 90) -> pd.DataFrame:
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
    
    def _calculate_rsi(self, df: pd.DataFrame, window: Optional[int] = None) -> Optional[float]:
        """
        计算 RSI 指标
        
        Args:
            df: 股票数据
            window: RSI 窗口（None 则使用参数）
            
        Returns:
            float: RSI 值（0-100），None 表示计算失败
        """
        if 'close' not in df.columns or len(df) < (window or self.parameters["rsi_window"]) + 1:
            return None
        
        window = window or self.parameters["rsi_window"]
        
        # 计算价格变化
        delta = df['close'].diff()
        
        # 分别计算上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # 计算 RS
        rs = avg_gain / avg_loss
        
        # 计算 RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def generate_signals(self, context: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号
        
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
        if self.parameters["rsi_window"] <= 0:
            self.logger.error("rsi_window 必须大于 0")
            return False
        
        if not (0 <= self.parameters["oversold"] <= 100):
            self.logger.error("oversold 必须在 0-100 之间")
            return False
        
        if not (0 <= self.parameters["overbought"] <= 100):
            self.logger.error("overbought 必须在 0-100 之间")
            return False
        
        if self.parameters["oversold"] >= self.parameters["overbought"]:
            self.logger.error("oversold 必须小于 overbought")
            return False
        
        if not self.parameters["stock_pool"]:
            self.logger.error("stock_pool 不能为空")
            return False
        
        return True
    
    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """
        返回默认参数
        
        Returns:
            Dict: 默认参数字典
        """
        return {
            "rsi_window": 14,
            "overbought": 70,
            "oversold": 30,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1,
            "description": "RSI 策略：RSI < 30 买入，RSI > 70 卖出"
        }
