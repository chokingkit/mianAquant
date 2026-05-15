"""
回测模块初始化
提供回测引擎、交易规则、订单执行器和结果分析器
"""
from app.backtest.engine import BacktestEngine
from app.backtest.rules import AShareTradingRules
from app.backtest.executor import OrderExecutor
from app.backtest.analyzer import BacktestAnalyzer

__all__ = ['BacktestEngine', 'AShareTradingRules', 'OrderExecutor', 'BacktestAnalyzer']
