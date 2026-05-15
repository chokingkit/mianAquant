"""
策略模块初始化
提供策略基类、预置策略的注册和管理
"""
from app.strategies.base import BaseStrategy
from app.strategies.template import CustomStrategyTemplate

__all__ = ['BaseStrategy', 'CustomStrategyTemplate']
