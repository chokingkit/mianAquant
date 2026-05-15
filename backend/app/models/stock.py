"""
股票数据模型（SQLAlchemy ORM）
定义 StockInfo 和 StockDailyData 表结构
"""
from typing import List, Dict, Any
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Index
from sqlalchemy.sql import func
from loguru import logger

from app.models.base import Base


class StockInfo(Base):
    """
    股票基本信息表
    
    存储股票的静态信息（每日更新或从 API 获取后缓存）
    """
    __tablename__ = 'stock_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True, comment='股票代码（格式: sh.600000）')
    name = Column(String(50), nullable=False, comment='股票名称')
    market = Column(String(10), nullable=False, index=True, comment='市场（SH/SZ/BJ）')
    industry = Column(String(100), comment='所属行业')
    area = Column(String(50), comment='地区')
    list_date = Column(Date, comment='上市日期')
    delist_date = Column(Date, comment='退市日期')
    is_listed = Column(Boolean, default=True, comment='是否上市')
    total_capital = Column(Float, comment='总股本（万股）')
    circulating_capital = Column(Float, comment='流通股本（万股）')
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_market_listed', 'market', 'is_listed'),
    )
    
    def __repr__(self) -> str:
        return f"<StockInfo(code={self.code}, name={self.name}, market={self.market})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'industry': self.industry,
            'area': self.area,
            'list_date': self.list_date.isoformat() if self.list_date else None,
            'delist_date': self.delist_date.isoformat() if self.delist_date else None,
            'is_listed': self.is_listed,
            'total_capital': self.total_capital,
            'circulating_capital': self.circulating_capital,
        }
    
    @classmethod
    def from_dataframe(cls, df: 'pd.DataFrame') -> List['StockInfo']:
        """
        从 DataFrame 创建实例列表
        
        Args:
            df: 包含股票信息的 DataFrame
            
        Returns:
            List[StockInfo]: 实例列表
        """
        instances = []
        
        for _, row in df.iterrows():
            instance = cls(
                code=row.get('code'),
                name=row.get('name'),
                market=row.get('market'),
                industry=row.get('industry'),
                area=row.get('area'),
                list_date=row.get('list_date'),
                is_listed=row.get('is_listed', True),
            )
            instances.append(instance)
        
        return instances


class StockDailyData(Base):
    """
    股票日线数据表
    
    存储股票的日线行情数据（可从 API 获取后缓存，
    或存储 qlib 处理后的特征数据）
    """
    __tablename__ = 'stock_daily_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True, comment='股票代码')
    date = Column(Date, nullable=False, index=True, comment='交易日期')
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    volume = Column(Float, comment='成交量（手）')
    amount = Column(Float, comment='成交额（元）')
    change = Column(Float, comment='涨跌幅（%）')
    turn_over = Column(Float, comment='换手率（%）')
    # qlib 特征列（可选）
    return_rate = Column(Float, comment='收益率')
    ma5 = Column(Float, comment='5日均线')
    ma10 = Column(Float, comment='10日均线')
    ma20 = Column(Float, comment='20日均线')
    ma60 = Column(Float, comment='60日均线')
    volatility_20 = Column(Float, comment='20日波动率')
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建复合索引（确保一只股票的某日数据唯一）
    __table_args__ = (
        Index('idx_code_date', 'code', 'date', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<StockDailyData(code={self.code}, date={self.date}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'date': self.date.isoformat() if self.date else None,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'change': self.change,
            'turn_over': self.turn_over,
            'return_rate': self.return_rate,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'volatility_20': self.volatility_20,
        }
    
    @classmethod
    def from_dataframe(cls, df: 'pd.DataFrame', code: str) -> List['StockDailyData']:
        """
        从 DataFrame 创建实例列表
        
        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            
        Returns:
            List[StockDailyData]: 实例列表
        """
        instances = []
        
        for _, row in df.iterrows():
            instance = cls(
                code=code,
                date=row.get('date'),
                open=row.get('open'),
                high=row.get('high'),
                low=row.get('low'),
                close=row.get('close'),
                volume=row.get('volume'),
                amount=row.get('amount'),
                change=row.get('change'),
                turn_over=row.get('turn_over'),
            )
            
            # 可选特征列
            if 'return' in row:
                instance.return_rate = row['return']
            if 'MA5' in row:
                instance.ma5 = row['MA5']
            if 'MA10' in row:
                instance.ma10 = row['MA10']
            if 'MA20' in row:
                instance.ma20 = row['MA20']
            if 'MA60' in row:
                instance.ma60 = row['MA60']
            
            instances.append(instance)
        
        return instances
