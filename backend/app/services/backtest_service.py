"""
回测服务
提供回测执行、结果查询等功能
"""
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.models.strategy import StrategyConfig
from app.models.backtest import BacktestResult
from app.strategies.base import BaseStrategy


class BacktestService:
    """
    回测服务
    
    提供回测相关功能：
    - run_backtest(): 运行回测
    - get_backtest_result(): 获取回测结果
    - list_backtest_results(): 列出所有回测结果
    - delete_backtest_result(): 删除回测结果
    """
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.logger = logger.bind(module="BacktestService")
        self.logger.info("✓ 回测服务初始化完成")
    
    def run_backtest(self, 
                    strategy_id: int, 
                    start_date: date, 
                    end_date: date, 
                    initial_cash: float = 100000.0,
                    stock_pool: Optional[List[str]] = None) -> Optional[BacktestResult]:
        """
        运行回测
        
        Args:
            strategy_id: 策略配置 ID
            start_date: 开始日期
            end_date: 结束日期
            initial_cash: 初始资金
            stock_pool: 股票池（None 则使用策略配置中的股票池）
            
        Returns:
            BacktestResult: 回测结果实例（None 表示失败）
        """
        from app.backtest.engine import BacktestEngine
        from app.backtest.analyzer import BacktestAnalyzer
        from app.services.strategy_service import StrategyService
        
        self.logger.info(f"开始回测: strategy_id={strategy_id}, {start_date} ~ {end_date}")
        
        # 1. 加载策略配置
        strategy_service = StrategyService(self.db)
        strategy_config = strategy_service.get_strategy(strategy_id)
        
        if not strategy_config:
            self.logger.error(f"策略配置未找到: ID={strategy_id}")
            return None
        
        # 2. 创建策略实例
        strategy = strategy_config.create_strategy_instance()
        
        if not strategy:
            self.logger.error(f"创建策略实例失败: {strategy_config.name}")
            return None
        
        # 3. 确定股票池
        if stock_pool is None:
            stock_pool = strategy_config.stock_pool or []
        
        if not stock_pool:
            self.logger.error("股票池为空，无法回测")
            return None
        
        # 4. 创建回测引擎
        engine = BacktestEngine(initial_cash=initial_cash)
        
        # 5. 运行回测
        try:
            backtest_result = engine.run_backtest(
                strategy=strategy,
                start=start_date,
                end=end_date,
                stock_pool=stock_pool
            )
        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            return None
        
        # 6. 分析结果
        analyzer = BacktestAnalyzer()
        analysis = analyzer.analyze(backtest_result)
        
        # 7. 保存结果到数据库
        result = BacktestResult(
            strategy_id=strategy_id,
            strategy_name=strategy_config.name,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            final_value=backtest_result.get("final_value"),
            total_return=backtest_result.get("total_return"),
            annual_return=analysis.get("metrics", {}).get("annual_return"),
            sharpe_ratio=analysis.get("metrics", {}).get("sharpe_ratio"),
            max_drawdown=analysis.get("metrics", {}).get("max_drawdown"),
            win_rate=analysis.get("metrics", {}).get("win_rate"),
            total_trades=analysis.get("metrics", {}).get("total_trades", 0),
            equity_curve=backtest_result.get("equity_curve"),
            trades=backtest_result.get("trades"),
            metrics=analysis.get("metrics"),
            status="completed",
            completed_at=datetime.now()
        )
        
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        self.logger.info(f"✓ 回测完成: ID={result.id}, 收益率={result.total_return:.2%}")
        return result
    
    def get_backtest_result(self, backtest_id: int) -> Optional[BacktestResult]:
        """
        获取回测结果
        
        Args:
            backtest_id: 回测结果 ID
            
        Returns:
            BacktestResult: 回测结果实例（None 表示未找到）
        """
        return self.db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    
    def list_backtest_results(self, 
                            strategy_id: Optional[int] = None, 
                            status: Optional[str] = None) -> List[BacktestResult]:
        """
        列出回测结果
        
        Args:
            strategy_id: 策略配置 ID（可选，用于过滤）
            status: 状态（可选，用于过滤）
            
        Returns:
            List[BacktestResult]: 回测结果列表
        """
        query = self.db.query(BacktestResult)
        
        # 过滤策略 ID
        if strategy_id:
            query = query.filter(BacktestResult.strategy_id == strategy_id)
        
        # 过滤状态
        if status:
            query = query.filter(BacktestResult.status == status)
        
        # 按创建时间降序排列
        query = query.order_by(BacktestResult.created_at.desc())
        
        return query.all()
    
    def delete_backtest_result(self, backtest_id: int) -> bool:
        """
        删除回测结果
        
        Args:
            backtest_id: 回测结果 ID
            
        Returns:
            bool: 是否删除成功
        """
        result = self.get_backtest_result(backtest_id)
        
        if not result:
            self.logger.warning(f"回测结果未找到: ID={backtest_id}")
            return False
        
        # 删除
        self.db.delete(result)
        self.db.commit()
        
        self.logger.info(f"✓ 删除回测结果: ID={backtest_id}")
        return True
    
    def generate_report(self, backtest_id: int) -> Optional[str]:
        """
        生成回测报告
        
        Args:
            backtest_id: 回测结果 ID
            
        Returns:
            str: 回测报告（None 表示失败）
        """
        from app.backtest.analyzer import BacktestAnalyzer
        
        # 获取回测结果
        result = self.get_backtest_result(backtest_id)
        
        if not result:
            self.logger.warning(f"回测结果未找到: ID={backtest_id}")
            return None
        
        # 转换为分析结果格式
        analysis_result = {
            "strategy_name": result.strategy_name,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_cash": result.initial_cash,
            "final_value": result.final_value,
            "total_return": result.total_return,
            "equity_curve": result.equity_curve,
            "trades": result.trades,
            "metrics": result.metrics
        }
        
        # 生成报告
        analyzer = BacktestAnalyzer()
        report = analyzer.generate_report(analysis_result)
        
        return report
