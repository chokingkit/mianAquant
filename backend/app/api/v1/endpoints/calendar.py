"""
交易日历 API 端点
提供交易日查询、日历数据等接口
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.data.factory import get_data_provider
from app.data.interface import DataProvider
from app.data.qlib_integration.calendar import AShareTradingCalendar

router = APIRouter()


@router.get("/", summary="获取交易日历")
async def get_trading_calendar(
    start_date: date = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    获取指定日期范围内的交易日列表
    
    - **start_date**: 开始日期
    - **end_date**: 结束日期（可选，默认到最新）
    - 返回交易日列表 JSON
    """
    try:
        logger.info(f"API 请求: 获取交易日历 ({start_date} ~ {end_date})")
        
        # 调用数据提供者
        trading_dates = provider.get_trading_calendar(start_date, end_date)
        
        if not trading_dates:
            raise HTTPException(status_code=404, detail="未找到交易日数据")
        
        # 转换为字符串列表
        result = [d.isoformat() for d in trading_dates]
        
        logger.info(f"✓ 返回交易日历: {len(result)} 个交易日")
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "total": len(result),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{check_date}", summary="检查是否为交易日")
async def check_trading_day(
    check_date: date,
    provider: DataProvider = Depends(get_data_provider)
):
    """
    检查指定日期是否为交易日
    
    - **check_date**: 要检查的日期
    - 返回检查结果 JSON
    """
    try:
        logger.info(f"API 请求: 检查日期 {check_date}")
        
        # 创建交易日历实例
        calendar = AShareTradingCalendar(provider=provider)
        
        # 检查是否为交易日
        is_trading = calendar.is_trading_day(check_date)
        
        logger.info(f"✓ 日期检查: {check_date} is_trading={is_trading}")
        return {
            "date": check_date.isoformat(),
            "is_trading_day": is_trading,
            "weekday": check_date.strftime("%A")
        }
        
    except Exception as e:
        logger.error(f"检查日期失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offset", summary="计算交易日偏移")
async def calculate_trading_day_offset(
    start_date: date = Query(..., description="开始日期"),
    offset: int = Query(..., description="偏移量（正数=向后，负数=向前）"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    计算 N 个交易日后的日期
    
    - **start_date**: 开始日期
    - **offset**: 偏移量（正数=向后，负数=向前）
    - 返回偏移后的日期 JSON
    """
    try:
        logger.info(f"API 请求: 计算交易日偏移 ({start_date}, offset={offset})")
        
        # 创建交易日历实例
        calendar = AShareTradingCalendar(provider=provider)
        
        # 计算偏移
        result_date = calendar.add_trading_days(start_date, offset)
        
        logger.info(f"✓ 交易日偏移: {start_date} + {offset} = {result_date}")
        return {
            "start_date": start_date.isoformat(),
            "offset": offset,
            "result_date": result_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"计算交易日偏移失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count", summary="统计交易日数量")
async def count_trading_days(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    统计两个日期之间的交易日数量
    
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - 返回交易日数量 JSON
    """
    try:
        logger.info(f"API 请求: 统计交易日数量 ({start_date} ~ {end_date})")
        
        # 创建交易日历实例
        calendar = AShareTradingCalendar(provider=provider)
        
        # 统计交易日
        count = calendar.count_trading_days(start_date, end_date)
        
        logger.info(f"✓ 交易日统计: {count} 个交易日")
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trading_days_count": count
        }
        
    except Exception as e:
        logger.error(f"统计交易日失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limit/{stock_code}", summary="计算涨跌停价格")
async def calculate_limit_price(
    stock_code: str,
    prev_close: float = Query(..., description="昨收价"),
    direction: str = Query("up", description="方向（up=涨停, down=跌停）")
):
    """
    计算股票的涨停价或跌停价
    
    - **stock_code**: 股票代码（格式: sh.600000）
    - **prev_close**: 昨收价
    - **direction**: 方向（up=涨停, down=跌停）
    - 返回涨跌停价格 JSON
    """
    try:
        logger.info(f"API 请求: 计算涨跌停价格 ({stock_code}, prev_close={prev_close}, direction={direction})")
        
        # 创建交易日历实例
        calendar = AShareTradingCalendar()
        
        # 计算涨跌停价格
        if direction.lower() == "up":
            limit_price = calendar.calculate_limit_price(stock_code, prev_close, up=True)
        else:
            limit_price = calendar.calculate_limit_price(stock_code, prev_close, up=False)
        
        logger.info(f"✓ 涨跌停价格: {stock_code} {direction}={limit_price}")
        return {
            "code": stock_code,
            "prev_close": prev_close,
            "direction": direction,
            "limit_price": limit_price
        }
        
    except Exception as e:
        logger.error(f"计算涨跌停价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
