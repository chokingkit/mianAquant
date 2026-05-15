"""
交易日历模型（SQLAlchemy ORM）
定义 TradingCalendar 表结构
"""
from typing import List, Dict, Any
from datetime import date, datetime
from sqlalchemy import Column, Integer, Date, String, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from app.models.base import Base


class TradingCalendar(Base):
    """
    交易日历表
    
    存储 A股交易日历（可从 API 获取后缓存）
    """
    __tablename__ = 'trading_calendar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_date = Column(Date, nullable=False, unique=True, index=True, comment='日期')
    is_trading_day = Column(Boolean, nullable=False, index=True, comment='是否为交易日')
    exchange = Column(String(10), default='SSE', comment='交易所（SSE/SZSE/BSE）')
    holiday_name = Column(String(50), comment='节假日名称（如果是节假日）')
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_date_exchange', 'calendar_date', 'exchange', unique=True),
        Index('idx_trading_day', 'is_trading_day', 'calendar_date'),
    )
    
    def __repr__(self) -> str:
        return f"<TradingCalendar(date={self.calendar_date}, is_trading={self.is_trading_day})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.calendar_date.isoformat() if self.calendar_date else None,
            'is_trading_day': self.is_trading_day,
            'exchange': self.exchange,
            'holiday_name': self.holiday_name,
        }
    
    @classmethod
    def from_date_list(cls, 
                           dates: List[date], 
                           exchange: str = 'SSE') -> List['TradingCalendar']:
        """
        从日期列表创建实例列表
        
        Args:
            dates: 交易日列表
            exchange: 交易所代码
            
        Returns:
            List[TradingCalendar]: 实例列表
        """
        instances = []
        
        for d in dates:
            instance = cls(
                calendar_date=d,
                is_trading_day=True,
                exchange=exchange
            )
            instances.append(instance)
        
        return instances
    
    @classmethod
    def mark_holidays(cls, 
                           start_date: date, 
                           end_date: date, 
                           trading_dates: List[date],
                           exchange: str = 'SSE') -> List['TradingCalendar']:
        """
        标记节假日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            trading_dates: 交易日列表
            exchange: 交易所代码
            
        Returns:
            List[TradingCalendar]: 完整日历实例列表
        """
        from datetime import timedelta
        
        instances = []
        current = start_date
        
        while current <= end_date:
            is_trading = current in trading_dates
            
            instance = cls(
                calendar_date=current,
                is_trading_day=is_trading,
                exchange=exchange,
                holiday_name=None if is_trading else 'Non-trading day'
            )
            instances.append(instance)
            
            current += timedelta(days=1)
        
        return instances
