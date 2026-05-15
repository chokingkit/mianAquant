"""
风险指标计算模块
计算各类风险指标（最大回撤、夏普比率、VaR 等）
"""
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from loguru import logger


class RiskMetrics:
    """
    风险指标计算类
    
    提供各类风险指标的计算方法
    """
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> Dict[str, float]:
        """
        计算最大回撤
        
        Args:
            equity_curve: 权益曲线（净值序列）
            
        Returns:
            Dict: 最大回撤相关信息
                - max_drawdown: 最大回撤比例
                - max_drawdown_amount: 最大回撤金额
                - max_drawdown_start: 回撤开始索引
                - max_drawdown_end: 回撤结束索引
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_amount': 0.0,
                'max_drawdown_start': 0,
                'max_drawdown_end': 0,
            }
        
        # 转换为 numpy 数组
        curve = np.array(equity_curve)
        
        # 计算累计最大值
        running_max = np.maximum.accumulate(curve)
        
        # 计算回撤
        drawdown = (running_max - curve) / running_max
        
        # 最大回撤
        max_dd = np.max(drawdown)
        max_dd_end = np.argmax(drawdown)
        max_dd_start = np.argmax(curve[:max_dd_end + 1]) if max_dd_end > 0 else 0
        
        max_dd_amount = running_max[max_dd_end] - curve[max_dd_end]
        
        return {
            'max_drawdown': float(max_dd),
            'max_drawdown_amount': float(max_dd_amount),
            'max_drawdown_start': int(max_dd_start),
            'max_drawdown_end': int(max_dd_end),
        }
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> Dict[str, float]:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列（日收益率）
            risk_free_rate: 无风险利率（年化）
            periods_per_year: 年化倍数（252 个交易日）
            
        Returns:
            Dict: 夏普比率相关信息
                - sharpe_ratio: 夏普比率
                - annual_return: 年化收益率
                - annual_volatility: 年化波动率
        """
        if not returns or len(returns) < 2:
            return {
                'sharpe_ratio': 0.0,
                'annual_return': 0.0,
                'annual_volatility': 0.0,
            }
        
        # 转换为 numpy 数组
        returns_array = np.array(returns)
        
        # 计算年化收益率
        mean_return = np.mean(returns_array)
        annual_return = mean_return * periods_per_year
        
        # 计算年化波动率
        volatility = np.std(returns_array, ddof=1)
        annual_volatility = volatility * np.sqrt(periods_per_year)
        
        # 计算夏普比率
        excess_return = annual_return - risk_free_rate
        sharpe = excess_return / annual_volatility if annual_volatility > 0 else 0.0
        
        return {
            'sharpe_ratio': float(sharpe),
            'annual_return': float(annual_return),
            'annual_volatility': float(annual_volatility),
        }
    
    @staticmethod
    def calculate_var(
        returns: List[float],
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> Dict[str, float]:
        """
        计算 VaR（Value at Risk，风险价值）
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平（默认 95%）
            method: 计算方法（目前仅支持 'historical'）
            
        Returns:
            Dict: VaR 相关信息
                - var: VaR 值（金额）
                - var_ratio: VaR 比例
                - cvar: CVaR（条件风险价值）
        """
        if not returns or len(returns) < 2:
            return {
                'var': 0.0,
                'var_ratio': 0.0,
                'cvar': 0.0,
            }
        
        returns_array = np.array(returns)
        
        if method == 'historical':
            # 历史模拟法
            var_ratio = np.percentile(returns_array, (1 - confidence_level) * 100)
            
            # 计算 CVaR（超过 VaR 的平均损失）
            cvar_mask = returns_array <= var_ratio
            cvar = np.mean(returns_array[cvar_mask]) if np.any(cvar_mask) else var_ratio
            
        else:
            # 默认使用历史模拟法
            logger.warning(f"⚠ 不支持的 VaR 计算方法: {method}，使用 historical")
            var_ratio = np.percentile(returns_array, (1 - confidence_level) * 100)
            cvar_mask = returns_array <= var_ratio
            cvar = np.mean(returns_array[cvar_mask]) if np.any(cvar_mask) else var_ratio
        
        return {
            'var': float(var_ratio),
            'var_ratio': float(var_ratio),
            'cvar': float(cvar),
            'confidence_level': confidence_level,
            'method': 'historical',
        }
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: List[float],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> Dict[str, float]:
        """
        计算索提诺比率（只考虑下行波动）
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）
            periods_per_year: 年化倍数
            
        Returns:
            Dict: 索提诺比率相关信息
        """
        if not returns or len(returns) < 2:
            return {
                'sortino_ratio': 0.0,
                'downside_deviation': 0.0,
            }
        
        returns_array = np.array(returns)
        
        # 计算下行偏差（只考虑负收益）
        mean_return = np.mean(returns_array)
        downside_returns = returns_array[returns_array < 0]
        
        if len(downside_returns) == 0:
            downside_deviation = 0.0
        else:
            downside_deviation = np.std(downside_returns, ddof=1)
        
        annual_downside = downside_deviation * np.sqrt(periods_per_year)
        annual_return = mean_return * periods_per_year
        
        excess_return = annual_return - risk_free_rate
        sortino = excess_return / annual_downside if annual_downside > 0 else 0.0
        
        return {
            'sortino_ratio': float(sortino),
            'annual_return': float(annual_return),
            'downside_deviation': float(annual_downside),
        }
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算胜率
        
        Args:
            trades: 交易记录列表，每条记录包含：
                - action: 操作（buy/sell）
                - profit: 盈亏（卖出时）
                
        Returns:
            Dict: 胜率相关信息
        """
        if not trades:
            return {
                'win_rate': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
            }
        
        # 提取有盈亏的交易
        profits = [t.get('profit', 0) for t in trades if t.get('action') == 'sell' and t.get('profit') is not None]
        
        if not profits:
            return {
                'win_rate': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
            }
        
        winning = [p for p in profits if p > 0]
        losing = [p for p in profits if p <= 0]
        
        win_rate = len(winning) / len(profits) if profits else 0.0
        avg_win = np.mean(winning) if winning else 0.0
        avg_loss = np.mean([abs(p) for p in losing]) if losing else 0.0
        
        total_win = sum(winning)
        total_loss = sum(abs(p) for p in losing)
        profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        
        return {
            'win_rate': float(win_rate),
            'total_trades': len(profits),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'profit_factor': float(profit_factor),
        }
    
    @staticmethod
    def calculate_all_metrics(
        equity_curve: List[float],
        returns: List[float],
        trades: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        计算所有风险指标
        
        Args:
            equity_curve: 权益曲线
            returns: 收益率序列
            trades: 交易记录（可选）
            
        Returns:
            Dict: 所有风险指标
        """
        metrics = {}
        
        # 最大回撤
        metrics['max_drawdown'] = RiskMetrics.calculate_max_drawdown(equity_curve)
        
        # 夏普比率
        metrics['sharpe'] = RiskMetrics.calculate_sharpe_ratio(returns)
        
        # 索提诺比率
        metrics['sortino'] = RiskMetrics.calculate_sortino_ratio(returns)
        
        # VaR
        metrics['var'] = RiskMetrics.calculate_var(returns)
        
        # 胜率（如果有交易记录）
        if trades:
            metrics['win_rate'] = RiskMetrics.calculate_win_rate(trades)
        
        logger.info(f"✓ 风险指标计算完成: Sharpe={metrics['sharpe']['sharpe_ratio']:.2f}, "
                    f"MaxDD={metrics['max_drawdown']['max_drawdown']:.2%}")
        
        return metrics
