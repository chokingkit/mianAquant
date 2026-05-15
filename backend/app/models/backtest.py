"""
回测结果模型（SQLAlchemy ORM）
定义 BacktestResult 和 Trade 表结构
"""
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from loguru import logger

from app.models.base import Base


class BacktestResult(Base):
    """
    回测结果表
    
    存储回测的结果（收益曲线、交易记录、性能指标）
    """
    __tablename__ = 'backtest_result'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, index=True, comment='策略配置 ID')
    strategy_name = Column(String(100), comment='策略名称')
    start_date = Column(Date, nullable=False, index=True, comment='回测开始日期')
    end_date = Column(Date, nullable=False, index=True, comment='回测结束日期')
    initial_cash = Column(Float, default=100000.0, comment='初始资金')
    final_value = Column(Float, comment='最终市值')
    total_return = Column(Float, comment='总收益率')
    annual_return = Column(Float, comment='年化收益率')
    sharpe_ratio = Column(Float, comment='夏普比率')
    max_drawdown = Column(Float, comment='最大回撤')
    win_rate = Column(Float, comment='胜率')
    total_trades = Column(Integer, default=0, comment='总交易次数')
    equity_curve = Column(JSON, comment='权益曲线（JSON 格式）')
    trades = Column(JSON, comment='交易记录（JSON 格式）')
    metrics = Column(JSON, comment='性能指标（JSON 格式）')
    status = Column(String(20), default='pending', index=True, comment='状态（pending/running/completed/failed）')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, comment='完成时间')
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_strategy_dates', 'strategy_id', 'start_date', 'end_date'),
    )
    
    def __repr__(self) -> str:
        return f"<BacktestResult(id={self.id}, strategy={self.strategy_name}, return={self.total_return})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_cash': self.initial_cash,
            'final_value': self.final_value,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'metrics': self.metrics,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_backtest_result(cls, 
                              backtest_result: Dict[str, Any], 
                              strategy_id: Optional[int] = None) -> 'BacktestResult':
        """
        从回测结果创建实例
        
        Args:
            backtest_result: 回测结果字典
            strategy_id: 策略配置 ID
            
        Returns:
            BacktestResult: 实例
        """
        return cls(
            strategy_id=strategy_id,
            strategy_name=backtest_result.get('strategy_name'),
            start_date=backtest_result.get('start_date'),
            end_date=backtest_result.get('end_date'),
            initial_cash=backtest_result.get('initial_cash'),
            final_value=backtest_result.get('final_value'),
            total_return=backtest_result.get('total_return'),
            annual_return=backtest_result.get('metrics', {}).get('annual_return'),
            sharpe_ratio=backtest_result.get('metrics', {}).get('sharpe_ratio'),
            max_drawdown=backtest_result.get('metrics', {}).get('max_drawdown'),
            win_rate=backtest_result.get('metrics', {}).get('win_rate'),
            total_trades=backtest_result.get('metrics', {}).get('total_trades'),
            equity_curve=backtest_result.get('equity_curve'),
            trades=backtest_result.get('trades'),
            metrics=backtest_result.get('metrics'),
            status='completed',
            completed_at=datetime.now()
        )


class Trade(Base):
    """
    交易记录表
    
    存储每笔交易的详细信息
    """
    __tablename__ = 'trade'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, index=True, comment='回测结果 ID')
    stock_code = Column(String(20), nullable=False, index=True, comment='股票代码')
    action = Column(String(10), nullable=False, comment='操作（buy/sell）')
    quantity = Column(Integer, nullable=False, comment='数量（股）')
    price = Column(Float, nullable=False, comment='价格')
    amount = Column(Float, comment='成交金额')
    commission = Column(Float, comment='佣金')
    slippage = Column(Float, comment='滑点成本')
    profit = Column(Float, comment='盈亏（卖出时）')
    reason = Column(String(200), comment='交易原因')
    timestamp = Column(Date, index=True, comment='交易日期')
    created_at = Column(DateTime, server_default=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_backtest_stock', 'backtest_id', 'stock_code'),
    )
    
    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, stock={self.stock_code}, action={self.action})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'backtest_id': self.backtest_id,
            'stock_code': self.stock_code,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'amount': self.amount,
            'commission': self.commission,
            'slippage': self.slippage,
            'profit': self.profit,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_trade_dict(cls, trade_dict: Dict[str, Any], backtest_id: int) -> 'Trade':
        """
        从交易字典创建实例
        
        Args:
            trade_dict: 交易字典
            backtest_id: 回测结果 ID
            
        Returns:
            Trade: 实例
        """
        return cls(
            backtest_id=backtest_id,
            stock_code=trade_dict.get('stock_code'),
            action=trade_dict.get('action'),
            quantity=trade_dict.get('quantity'),
            price=trade_dict.get('price'),
            amount=trade_dict.get('amount'),
            commission=trade_dict.get('commission'),
            slippage=trade_dict.get('slippage'),
            profit=trade_dict.get('profit'),
            reason=trade_dict.get('reason'),
            timestamp=trade_dict.get('timestamp')
        )
