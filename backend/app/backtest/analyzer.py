"""
回测结果分析器
计算性能指标、生成报告、可视化
"""
from typing import Dict, Any, List, Optional
from datetime import date
import pandas as pd
import numpy as np
from loguru import logger


class BacktestAnalyzer:
    """
    回测结果分析器
    
    功能：
    1. 计算性能指标（夏普比率、最大回撤等）
    2. 生成回测报告
    3. 分析交易记录
    4. 生成可视化数据
    """
    
    def __init__(self):
        """初始化分析器"""
        self.logger = logger.bind(module="BacktestAnalyzer")
        self.logger.info("✓ 回测分析器初始化完成")
    
    def analyze(self, backtest_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析回测结果
        
        Args:
            backtest_result: 回测结果字典
            
        Returns:
            Dict: 分析结果（包含详细指标）
        """
        self.logger.info(f"开始分析回测结果: {backtest_result.get('strategy_name')}")
        
        # 提取数据
        equity_curve = backtest_result.get("equity_curve", [])
        trades = backtest_result.get("trades", [])
        initial_cash = backtest_result.get("initial_cash", 100000.0)
        
        if not equity_curve:
            self.logger.warning("权益曲线为空，无法分析")
            return {"error": "No equity curve data"}
        
        # 计算性能指标
        metrics = self._calculate_detailed_metrics(equity_curve, trades, initial_cash)
        
        # 分析交易记录
        trade_analysis = self._analyze_trades(trades)
        
        # 生成月度收益
        monthly_returns = self._calculate_monthly_returns(equity_curve)
        
        # 生成回撤分析
        drawdown_analysis = self._analyze_drawdown(equity_curve)
        
        result = {
            "strategy_name": backtest_result.get("strategy_name"),
            "start_date": backtest_result.get("start_date"),
            "end_date": backtest_result.get("end_date"),
            "initial_cash": initial_cash,
            "final_value": backtest_result.get("final_value"),
            "total_return": backtest_result.get("total_return"),
            "metrics": metrics,
            "trade_analysis": trade_analysis,
            "monthly_returns": monthly_returns,
            "drawdown_analysis": drawdown_analysis,
            "equity_curve": equity_curve,
            "trades": trades
        }
        
        self.logger.info(f"✓ 回测分析完成: 收益率={metrics.get('total_return', 0):.2%}, 夏普={metrics.get('sharpe_ratio', 0):.2f}")
        
        return result
    
    def _calculate_detailed_metrics(self, 
                                equity_curve: List[Dict], 
                                trades: List[Dict], 
                                initial_cash: float) -> Dict[str, float]:
        """
        计算详细的性能指标
        
        Args:
            equity_curve: 权益曲线
            trades: 交易记录
            initial_cash: 初始资金
            
        Returns:
            Dict: 性能指标字典
        """
        # 转换为 DataFrame
        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # 计算日收益率
        df['daily_return'] = df['equity'].pct_change()
        
        # 总收益率
        final_value = df['equity'].iloc[-1]
        total_return = (final_value - initial_cash) / initial_cash
        
        # 年化收益率
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 夏普比率（假设无风险利率 2.5%）
        risk_free_rate = 0.025 / 252  # 日化
        excess_returns = df['daily_return'] - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / df['daily_return'].std()) * np.sqrt(252) if df['daily_return'].std() > 0 else 0
        
        # 最大回撤
        df['cumulative'] = (1 + df['daily_return']).cumprod()
        df['running_max'] = df['cumulative'].cummax()
        df['drawdown'] = (df['cumulative'] - df['running_max']) / df['running_max']
        max_drawdown = df['drawdown'].min()
        
        # 胜率
        if trades:
            winning_trades = [t for t in trades if t.get('profit', 0) > 0]
            win_rate = len(winning_trades) / len(trades)
        else:
            win_rate = 0.0
        
        # 平均盈利 / 平均亏损
        profits = [t['profit'] for t in trades if t.get('profit', 0) > 0]
        losses = [abs(t['profit']) for t in trades if t.get('profit', 0) < 0]
        
        avg_profit = np.mean(profits) if profits else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0.0
        
        # 波动率（年化）
        volatility = df['daily_return'].std() * np.sqrt(252)
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "volatility": volatility,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "total_trades": len(trades)
        }
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """
        分析交易记录
        
        Args:
            trades: 交易记录列表
            
        Returns:
            Dict: 交易分析
        """
        if not trades:
            return {"total_trades": 0}
        
        # 分离买入和卖出
        buy_trades = [t for t in trades if t.get('action') == 'buy']
        sell_trades = [t for t in trades if t.get('action') == 'sell']
        
        # 计算盈亏分布
        profits = [t.get('profit', 0) for t in sell_trades]
        
        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_profit": sum(profits),
            "avg_profit_per_trade": np.mean(profits) if profits else 0.0,
            "max_profit": max(profits) if profits else 0.0,
            "max_loss": min(profits) if profits else 0.0
        }
    
    def _calculate_monthly_returns(self, equity_curve: List[Dict]) -> List[Dict]:
        """
        计算月度收益
        
        Args:
            equity_curve: 权益曲线
            
        Returns:
            List[Dict]: 月度收益列表
        """
        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # 按月重采样
        monthly = df['equity'].resample('M').last()
        monthly_returns = monthly.pct_change().dropna()
        
        result = []
        for date, ret in monthly_returns.items():
            result.append({
                "month": date.strftime('%Y-%m'),
                "return": ret
            })
        
        return result
    
    def _analyze_drawdown(self, equity_curve: List[Dict]) -> Dict[str, Any]:
        """
        分析回撤
        
        Args:
            equity_curve: 权益曲线
            
        Returns:
            Dict: 回撤分析
        """
        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # 计算回撤
        df['cumulative'] = (1 + df['equity'].pct_change()).cumprod()
        df['running_max'] = df['cumulative'].cummax()
        df['drawdown'] = (df['cumulative'] - df['running_max']) / df['running_max']
        
        # 找到最大回撤期间
        max_dd_idx = df['drawdown'].idxmin()
        max_dd_start = df[df['drawdown'] == 0].index[-1] if (df['drawdown'] == 0).any() else df.index[0]
        
        return {
            "max_drawdown": df['drawdown'].min(),
            "max_drawdown_date": max_dd_idx.strftime('%Y-%m-%d'),
            "max_drawdown_start": max_dd_start.strftime('%Y-%m-%d'),
            "current_drawdown": df['drawdown'].iloc[-1]
        }
    
    def generate_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成回测报告（文本格式）
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 回测报告
        """
        metrics = analysis_result.get("metrics", {})
        trade_analysis = analysis_result.get("trade_analysis", {})
        
        report = f"""
{'='*60}
回测报告
{'='*60}

策略名称: {analysis_result.get('strategy_name')}
回测期间: {analysis_result.get('start_date')} ~ {analysis_result.get('end_date')}
初始资金: {analysis_result.get('initial_cash', 0):,.2f} 元
最终市值: {analysis_result.get('final_value', 0):,.2f} 元

{'─'*60}
性能指标
{'─'*60}
总收益率: {metrics.get('total_return', 0):.2%}
年化收益率: {metrics.get('annual_return', 0):.2%}
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
最大回撤: {metrics.get('max_drawdown', 0):.2%}
波动率（年化): {metrics.get('volatility', 0):.2%}
胜率: {metrics.get('win_rate', 0):.2%}
盈亏比: {metrics.get('profit_loss_ratio', 0):.2f}

{'─'*60}
交易分析
{'─'*60}
总交易次数: {trade_analysis.get('total_trades', 0)}
买入次数: {trade_analysis.get('buy_trades', 0)}
卖出次数: {trade_analysis.get('sell_trades', 0)}
总盈亏: {trade_analysis.get('total_profit', 0):,.2f} 元
平均单笔盈利: {trade_analysis.get('avg_profit_per_trade', 0):,.2f} 元
最大单笔盈利: {trade_analysis.get('max_profit', 0):,.2f} 元
最大单笔亏损: {trade_analysis.get('max_loss', 0):,.2f} 元

{'='*60}
"""
        
        return report
    
    def export_to_dataframe(self, analysis_result: Dict[str, Any]) -> pd.DataFrame:
        """
        导出权益曲线为 DataFrame
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            DataFrame: 权益曲线
        """
        equity_curve = analysis_result.get("equity_curve", [])
        
        if not equity_curve:
            return pd.DataFrame()
        
        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        return df
