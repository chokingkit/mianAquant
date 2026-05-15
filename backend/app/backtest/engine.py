"""
回测引擎（事件驱动）
按交易日迭代，调用策略生成信号，执行订单，计算收益
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime
import pandas as pd
import numpy as np
from loguru import logger

from app.backtest.rules import AShareTradingRules
from app.backtest.executor import OrderExecutor
from app.data.factory import DataProviderFactory


class Portfolio:
    """
    投资组合类
    
    属性：
    - cash: 可用资金
    - positions: 持仓字典 {stock_code: quantity}
    - cost_basis: 持仓成本 {stock_code: avg_cost}
    - trades: 交易记录列表
    - current_date: 当前日期
    """
    
    def __init__(self, initial_cash: float = 100000.0):
        """
        初始化投资组合
        
        Args:
            initial_cash: 初始资金（元）
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}       # {stock_code: quantity}
        self.cost_basis = {}      # {stock_code: avg_cost}
        self.trades = []          # 交易记录
        self.current_date = None   # 当前日期
        self.daily_values = []    # 每日市值记录
        
        self.logger = logger.bind(module="Portfolio")
        self.logger.info(f"✓ 投资组合初始化: 初始资金 {initial_cash:,.2f} 元")
    
    def mark_to_market(self, market_data: pd.DataFrame) -> float:
        """
        按市价计算组合总市值
        
        Args:
            market_data: 市场数据 DataFrame（包含当日收盘价）
            
        Returns:
            float: 组合总市值
        """
        # 计算持仓市值
        positions_value = 0.0
        
        for stock_code, quantity in self.positions.items():
            # 获取当日收盘价
            stock_data = market_data[market_data['code'] == stock_code] if 'code' in market_data.columns else pd.DataFrame()
            
            if not stock_data.empty:
                current_price = stock_data.iloc[0]['close']
                positions_value += quantity * current_price
            else:
                # 无法获取价格，使用成本价估算
                cost = self.cost_basis.get(stock_code, 0.0)
                positions_value += quantity * cost
        
        # 总市值 = 现金 + 持仓市值
        total_value = self.cash + positions_value
        
        # 记录每日市值
        self.daily_values.append({
            'date': self.current_date,
            'cash': self.cash,
            'positions_value': positions_value,
            'total_value': total_value
        })
        
        return total_value
    
    def get_total_value(self, market_data: Optional[pd.DataFrame] = None) -> float:
        """
        获取组合总市值
        
        Args:
            market_data: 市场数据（可选）
            
        Returns:
            float: 组合总市值
        """
        if market_data is not None:
            return self.mark_to_market(market_data)
        
        # 使用最近一次计算的市值
        if self.daily_values:
            return self.daily_values[-1]['total_value']
        
        return self.cash
    
    def get_positions_value(self, market_data: pd.DataFrame) -> float:
        """
        获取持仓市值
        
        Args:
            market_data: 市场数据
            
        Returns:
            float: 持仓市值
        """
        positions_value = 0.0
        
        for stock_code, quantity in self.positions.items():
            stock_data = market_data[market_data['code'] == stock_code] if 'code' in market_data.columns else pd.DataFrame()
            
            if not stock_data.empty:
                current_price = stock_data.iloc[0]['close']
                positions_value += quantity * current_price
        
        return positions_value
    
    def get_return_rate(self) -> float:
        """
        获取总收益率
        
        Returns:
            float: 收益率（如 0.15 = 15%）
        """
        current_value = self.get_total_value()
        return (current_value - self.initial_cash) / self.initial_cash
    
    def get_trades_count(self) -> int:
        """
        获取交易次数
        
        Returns:
            int: 交易次数
        """
        return len(self.trades)
    
    def get_win_rate(self) -> float:
        """
        获取胜率
        
        Returns:
            float: 胜率（0-1）
        """
        if not self.trades:
            return 0.0
        
        winning_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        return len(winning_trades) / len(self.trades)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict: 投资组合状态
        """
        return {
            'initial_cash': self.initial_cash,
            'cash': self.cash,
            'positions': self.positions.copy(),
            'cost_basis': self.cost_basis.copy(),
            'total_value': self.get_total_value(),
            'return_rate': self.get_return_rate(),
            'trades_count': self.get_trades_count()
        }


class BacktestEngine:
    """
    回测引擎（事件驱动）
    
    功能：
    1. 按交易日迭代
    2. 调用策略生成交易信号
    3. 执行订单（应用 A股规则）
    4. 计算收益曲线和性能指标
    """
    
    def __init__(self, 
                 initial_cash: float = 100000.0, 
                 commission: float = 0.0003, 
                 slippage: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金（元）
            commission: 佣金费率（万3 = 0.0003）
            slippage: 滑点（0.1% = 0.001）
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage
        
        self.rules = AShareTradingRules.get_instance()
        self.executor = OrderExecutor(commission=commission, slippage=slippage)
        
        self.logger = logger.bind(module="BacktestEngine")
        self.logger.info(f"✓ 回测引擎初始化: 初始资金={initial_cash:,.2f}, 佣金={commission:.4f}, 滑点={slippage:.4f}")
    
    def run_backtest(self, 
                    strategy: Any, 
                    start: date, 
                    end: date, 
                    stock_pool: List[str],
                    data_provider: Optional[Any] = None) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            strategy: 策略实例（继承自 BaseStrategy）
            start: 开始日期
            end: 结束日期
            stock_pool: 股票池
            data_provider: 数据提供者（None 则使用默认）
            
        Returns:
            Dict: 回测结果
                {
                    "strategy_name": "...",
                    "start_date": date,
                    "end_date": date,
                    "initial_cash": float,
                    "final_value": float,
                    "total_return": float,
                    "equity_curve": List[Dict],
                    "trades": List[Dict],
                    "metrics": Dict
                }
        """
        self.logger.info(f"开始回测: 策略={strategy.name}, 时间={start} ~ {end}")
        
        # 1. 初始化
        if data_provider is None:
            data_provider = DataProviderFactory.get_instance().get_provider("tushare")
        
        portfolio = Portfolio(self.initial_cash)
        context = {
            "start_date": start,
            "end_date": end,
            "current_date": None,
            "portfolio": portfolio,
            "data_provider": data_provider,
            "signals": {}
        }
        
        # 2. 调用策略初始化
        strategy.initialize(context)
        
        # 3. 获取交易日历
        trading_days = data_provider.get_trading_calendar(start, end)
        
        if not trading_days:
            self.logger.error("未找到交易日，回测终止")
            return self._empty_result(strategy.name, start, end)
        
        self.logger.info(f"获取到 {len(trading_days)} 个交易日")
        
        # 4. 按交易日迭代
        equity_curve = []
        trades = []
        
        for current_date in trading_days:
            context["current_date"] = current_date
            portfolio.current_date = current_date
            
            # 获取当前交易日的市场数据
            data = self._get_market_data(data_provider, stock_pool, current_date)
            
            if data.empty:
                self.logger.warning(f"交易日 {current_date} 无市场数据")
                continue
            
            # 调用策略处理数据
            strategy.handle_data(context, data)
            
            # 执行交易信号
            signals = context.get("signals", {})
            
            for stock_code, signal in signals.items():
                order = {
                    "stock_code": stock_code,
                    "action": signal["action"],
                    "quantity": signal["quantity"],
                    "price": signal.get("price", self._get_execution_price(data, stock_code)),
                    "signal_date": current_date,
                    "execution_date": current_date,
                    "reason": signal.get("reason", "")
                }
                
                # 验证订单（应用 A股规则）
                is_valid, reason, adjusted_order = self.rules.validate_order(
                    order, portfolio, None
                )
                
                if not is_valid:
                    self.logger.warning(f"订单无效: {reason}")
                    continue
                
                # 执行订单
                trade = self.executor.execute_order(adjusted_order, portfolio, self.commission, self.slippage)
                
                if trade:
                    trades.append(trade)
            
            # 清空信号（下一个交易日重新生成）
            context["signals"] = {}
            
            # 标记组合市值（按当日收盘价）
            portfolio.mark_to_market(data)
            equity_curve.append({
                "date": current_date,
                "equity": portfolio.get_total_value()
            })
        
        # 5. 计算回测指标
        metrics = self._calculate_metrics(equity_curve, trades, self.initial_cash)
        
        # 6. 返回结果
        result = {
            "strategy_name": strategy.name,
            "start_date": start,
            "end_date": end,
            "initial_cash": self.initial_cash,
            "final_value": portfolio.get_total_value(),
            "total_return": (portfolio.get_total_value() - self.initial_cash) / self.initial_cash,
            "equity_curve": equity_curve,
            "trades": trades,
            "metrics": metrics,
            "portfolio": portfolio.to_dict()
        }
        
        self.logger.info(f"✓ 回测完成: 收益率={result['total_return']:.2%}, 夏普={metrics.get('sharpe_ratio', 0):.2f}")
        
        return result
    
    def _get_market_data(self, 
                         data_provider: Any, 
                         stock_pool: List[str], 
                         current_date: date) -> pd.DataFrame:
        """
        获取多个股票在指定日期的数据
        
        Args:
            data_provider: 数据提供者
            stock_pool: 股票池
            current_date: 当前日期
            
        Returns:
            DataFrame: 市场数据
        """
        all_data = []
        
        for stock_code in stock_pool:
            try:
                # 获取最近两天的数据（用于计算指标）
                df = data_provider.get_stock_daily(
                    stock_code, 
                    current_date - pd.Timedelta(days=1), 
                    current_date
                )
                
                if not df.empty:
                    latest = df.iloc[-1]
                    latest_data = {
                        'code': stock_code,
                        'date': latest['date'] if 'date' in df.columns else current_date,
                        'open': latest['open'],
                        'high': latest['high'],
                        'low': latest['low'],
                        'close': latest['close'],
                        'volume': latest['volume'],
                        'amount': latest['amount']
                    }
                    all_data.append(latest_data)
            except Exception as e:
                self.logger.error(f"获取股票 {stock_code} 数据失败: {e}")
                continue
        
        return pd.DataFrame(all_data)
    
    def _get_execution_price(self, data: pd.DataFrame, stock_code: str) -> float:
        """
        获取执行价格（简化：使用收盘价）
        
        Args:
            data: 市场数据
            stock_code: 股票代码
            
        Returns:
            float: 执行价格
        """
        stock_data = data[data['code'] == stock_code]
        
        if not stock_data.empty:
            return stock_data.iloc[0]['close']
        
        return 0.0
    
    def _calculate_metrics(self, 
                         equity_curve: List[Dict], 
                         trades: List[Dict], 
                         initial_cash: float) -> Dict[str, float]:
        """
        计算回测性能指标
        
        Args:
            equity_curve: 权益曲线
            trades: 交易记录
            initial_cash: 初始资金
            
        Returns:
            Dict: 性能指标
        """
        if not equity_curve:
            return {}
        
        # 转换为 DataFrame
        equity_df = pd.DataFrame(equity_curve).set_index('date')
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # 剔除第一个 NaN
        returns = equity_df['returns'].dropna()
        
        if len(returns) == 0:
            return {}
        
        # 总收益率
        total_return = (equity_df['equity'].iloc[-1] - initial_cash) / initial_cash
        
        # 年化收益率
        trading_days = len(equity_curve)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
        
        # 夏普比率（假设无风险利率 2.5%）
        risk_free_rate = 0.025 / 252  # 日化
        excess_returns = returns - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 胜率
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # 平均盈利 / 平均亏损
        profits = [t.get('profit', 0) for t in trades if t.get('profit', 0) > 0]
        losses = [abs(t.get('profit', 0)) for t in trades if t.get('profit', 0) < 0]
        
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "total_trades": len(trades)
        }
    
    def _empty_result(self, strategy_name: str, start: date, end: date) -> Dict[str, Any]:
        """
        返回空结果（回测失败时）
        
        Args:
            strategy_name: 策略名称
            start: 开始日期
            end: 结束日期
            
        Returns:
            Dict: 空结果
        """
        return {
            "strategy_name": strategy_name,
            "start_date": start,
            "end_date": end,
            "initial_cash": self.initial_cash,
            "final_value": self.initial_cash,
            "total_return": 0.0,
            "equity_curve": [],
            "trades": [],
            "metrics": {},
            "portfolio": {"cash": self.initial_cash, "positions": {}, "return_rate": 0.0}
        }
