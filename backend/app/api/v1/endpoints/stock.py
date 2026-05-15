"""
股票数据 API 端点
提供股票列表、日线数据、实时行情等接口
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
import pandas as pd

from app.data.factory import get_data_provider
from app.data.interface import DataProvider
from app.models.stock import StockInfo, StockDailyData

router = APIRouter()


@router.get("/", summary="获取股票列表")
async def get_stock_list(
    market: Optional[str] = Query(None, description="市场代码（SH/SZ/BJ）"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    获取股票列表
    
    - **market**: 可选，过滤指定市场的股票
    - 返回股票列表 JSON
    """
    try:
        logger.info(f"API 请求: 获取股票列表 (market={market})")
        
        # 调用数据提供者
        df = provider.get_stock_list(market=market)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="未找到股票数据")
        
        # 转换为字典列表
        result = df.to_dict(orient='records')
        
        logger.info(f"✓ 返回股票列表: {len(result)} 只")
        return {
            "total": len(result),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/daily", summary="获取股票日线数据")
async def get_stock_daily(
    stock_code: str,
    start_date: date = Query(..., description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[date] = Query(None, description="结束日期（YYYY-MM-DD）"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    获取股票日线数据
    
    - **stock_code**: 股票代码（格式: sh.600000）
    - **start_date**: 开始日期
    - **end_date**: 结束日期（可选，默认到最新）
    - 返回日线数据 JSON
    """
    try:
        logger.info(f"API 请求: 获取股票 {stock_code} 日线数据 ({start_date} ~ {end_date})")
        
        # 调用数据提供者
        df = provider.get_stock_daily(stock_code, start_date, end_date)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的日线数据")
        
        # 转换日期列为字符串（JSON 序列化）
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # 转换为字典列表
        result = df.to_dict(orient='records')
        
        logger.info(f"✓ 返回日线数据: {len(result)} 条")
        return {
            "code": stock_code,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "total": len(result),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime", summary="获取实时行情")
async def get_stock_realtime(
    codes: Optional[str] = Query(None, description="股票代码列表（逗号分隔）"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    获取股票实时行情
    
    - **codes**: 可选，股票代码列表（如 "sh.600000,sz.000001"）
    - 返回实时行情 JSON
    """
    try:
        logger.info(f"API 请求: 获取实时行情 (codes={codes})")
        
        # 解析股票代码列表
        stock_codes = None
        if codes:
            stock_codes = [code.strip() for code in codes.split(',')]
        
        # 调用数据提供者
        df = provider.get_stock_realtime(stock_codes)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="未找到实时行情数据")
        
        # 转换时间列为字符串
        if 'time' in df.columns:
            df['time'] = df['time'].astype(str)
        
        # 转换为字典列表
        result = df.to_dict(orient='records')
        
        logger.info(f"✓ 返回实时行情: {len(result)} 条")
        return {
            "timestamp": datetime.now().isoformat(),
            "total": len(result),
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/info", summary="获取股票信息")
async def get_stock_info(
    stock_code: str,
    provider: DataProvider = Depends(get_data_provider)
):
    """
    获取股票基本信息
    
    - **stock_code**: 股票代码（格式: sh.600000）
    - 返回股票详细信息 JSON
    """
    try:
        logger.info(f"API 请求: 获取股票 {stock_code} 信息")
        
        # 调用数据提供者
        info = provider.get_stock_info(stock_code)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的信息")
        
        logger.info(f"✓ 返回股票信息: {stock_code}")
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="搜索股票")
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词（股票代码或名称）"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    provider: DataProvider = Depends(get_data_provider)
):
    """
    搜索股票（按代码或名称模糊匹配）
    
    - **keyword**: 搜索关键词
    - **limit**: 返回数量限制（1-100）
    - 返回匹配的股票列表 JSON
    """
    try:
        logger.info(f"API 请求: 搜索股票 (keyword={keyword})")
        
        # 获取全部股票列表
        df = provider.get_stock_list()
        
        if df.empty:
            return {"total": 0, "data": []}
        
        # 模糊匹配
        mask = df['code'].str.contains(keyword, na=False) | \
               df['name'].str.contains(keyword, na=False)
        filtered = df[mask].head(limit)
        
        # 转换为字典列表
        result = filtered.to_dict(orient='records')
        
        logger.info(f"✓ 搜索结果: {len(result)} 条")
        return {
            "keyword": keyword,
            "total": len(result),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
