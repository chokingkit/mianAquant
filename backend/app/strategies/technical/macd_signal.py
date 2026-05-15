"""
MACD 信号策略
基于 MACD 指标生成交易信号
"""
from typing import Dict, Any, Optional
from datetime import date
import pandas as pd
from loguru import logger

from app.strategies.base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD 策略
    
    策略逻辑：
    - MACD 线上穿信号线 → 买入信号（金叉）
    - MACD 线下穿信号线 → 卖出信号（死叉）
    
    参数：
    - short_window: 短期 EMA 窗口（默认 12）
    - long_window: 长期 EMA 窗口（默认 26）
    - signal_window: 信号线窗口（默认 9）
    - stock_pool: 股票池
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        初始化 MACD 策略
        
        Args:
            parameters: 策略参数字典
        """
        # 设置默认参数
        default_params = {
            "short_window": 12,
            "long_window": 26,
            "signal_window": 9,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1
        }
        
        # 用用户参数覆盖默认参数
        if parameters:
            default_params.update(parameters)
        
        super().__init__("MACDStrategy", default_params)
        
        # 验证参数
        if self.parameters["short_window"] >= self.parameters["long_window"]:
            raise ValueError("short_window 必须小于 long_window")
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        初始化策略
        
        Args:
            context: 上下文字典
        """
        self.context = context
        self.data_provider = context.get("data_provider")
        
        # 获取历史数据用于计算 MACD
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
        
        self.logger.info(f"✓ MACD 策略初始化完成，股票池: {len(self.parameters['stock_pool'])} 只")
    
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
            # 获取股票数据
            stock_data = self._get_stock_data(stock_code, current_date)
            
            if len(stock_data) < self.parameters["long_window"] + self.parameters["signal_window"]:
                self.logger.debug(f"股票 {stock_code} 数据不足，跳过")
                continue
            
            # 计算 MACD
            macd_line, signal_line, histogram = self._calculate_macd(stock_data)
            
            if len(macd_line) < 2:
                continue
            
            # 判断交叉
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            
            current_position = portfolio.positions.get(stock_code, 0)
            
            # 金叉（MACD 线上穿信号线）→ 买入
            if prev_macd <= prev_signal and current_macd > current_signal:
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
                            "reason": f"MACD golden cross: MACD={current_macd:.4f}, signal={current_signal:.4f}"
                        }
                        self.logger.info(f"生成买入信号: {stock_code}, MACD 金叉")
            
            # 死叉（MACD 线下穿信号线）→ 卖出
            elif prev_macd >= prev_signal and current_macd < current_signal:
                if current_position > 0:
                    signals[stock_code] = {
                        "action": "sell", 
                        "quantity": current_position,
                        "price": stock_data['close'].iloc[-1],
                        "reason": f"MACD death cross: MACD={current_macd:.4f}, signal={current_signal:.4f}"
                    }
                    self.logger.info(f"生成卖出信号: {stock_code}, MACD 死叉")
            
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
    
    def _calculate_macd(self, df: pd.DataFrame) -> tuple:
        """
        计算 MACD 指标
        
        Args:
            df: 股票数据 DataFrame
            
        Returns:
            tuple: (MACD线, 信号线, 柱状图)
        """
        if 'close' not in df.columns or df.empty:
            return pd.Series(), pd.Series(), pd.Series()
        
        # 计算 EMA
        ema_short = df['close'].ewm(span=self.parameters["short_window"], adjust=False).mean()
        ema_long = df['close'].ewm(span=self.parameters["long_window"], adjust=False).mean()
        
        # 计算 MACD 线
        macd_line = ema_short - ema_long
        
        # 计算信号线
        signal_line = macd_line.ewm(span=self.parameters["signal_window"], adjust=False).mean()
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
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
        if self.parameters["short_window"] <= 0:
            self.logger.error("short_window 必须大于 0")
            return False
        
        if self.parameters["long_window"] <= 0:
            self.logger.error("long_window 必须大于 0")
            return False
        
        if self.parameters["signal_window"] <= 0:
            self.logger.error("signal_window 必须大于 0")
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
        返回默认参数
        
        Returns:
            Dict: 默认参数字典
        """
        return {
            "short_window": 12,
            "long_window": 26,
            "signal_window": 9,
            "stock_pool": ["sh.600000", "sz.000001"],
            "max_position_pct": 0.1,
            "description": "MACD 策略：MACD 线上穿信号线买入，下穿卖出"
        }
