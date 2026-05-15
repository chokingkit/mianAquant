"""
回测异步任务
定义 run_backtest_task 等异步任务
"""
from typing import Dict, Any, Optional
from datetime import date, datetime
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models.base import Base
from app.models.backtest import BacktestResult

# 创建数据库会话（用于 Celery worker）
settings = get_settings()
engine = create_engine(
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_server}:{settings.postgres_port}/{settings.postgres_db}",
    pool_pre_ping=True,
)
SessionLocal = scoped_session(sessionmaker(bind=engine))


@celery_app.task(bind=True)
def run_backtest_task(self, 
                     strategy_id: int,
                     start_date_str: str,
                     end_date_str: str,
                     initial_cash: float = 100000.0,
                     stock_pool: Optional[list] = None) -> Dict[str, Any]:
    """
    异步执行回测任务
    
    Args:
        strategy_id: 策略配置 ID
        start_date_str: 开始日期（ISO 格式字符串）
        end_date_str: 结束日期（ISO 格式字符串）
        initial_cash: 初始资金
        stock_pool: 股票池
        
    Returns:
        Dict: 回测结果摘要
    """
    from app.backtest.engine import BacktestEngine
    from app.strategies.base import BaseStrategy
    from app.models.strategy import StrategyConfig
    from app.backtest.analyzer import BacktestAnalyzer
    
    task_id = self.request.id
    logger.info(f"[{task_id}] 开始异步回测: strategy_id={strategy_id}")
    
    # 更新任务状态
    self.update_state(
        state="PROGRESS",
        meta={"status": "正在初始化..."}
    )
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 1. 创建 BacktestResult 记录（pending 状态）
        backtest_record = BacktestResult(
            strategy_id=strategy_id,
            start_date=date.fromisoformat(start_date_str),
            end_date=date.fromisoformat(end_date_str),
            initial_cash=initial_cash,
            status="running",
            created_at=datetime.now(),
        )
        db.add(backtest_record)
        db.commit()
        db.refresh(backtest_record)
        
        logger.info(f"[{task_id}] 创建回测记录: ID={backtest_record.id}")
        
        # 2. 加载策略配置
        self.update_state(
            state="PROGRESS",
            meta={"status": "正在加载策略..."}
        )
        
        strategy_config = db.query(StrategyConfig).filter(
            StrategyConfig.id == strategy_id
        ).first()
        
        if not strategy_config:
            raise ValueError(f"策略配置未找到: ID={strategy_id}")
        
        # 3. 创建策略实例
        strategy = strategy_config.create_strategy_instance()
        if not strategy:
            raise ValueError(f"创建策略实例失败: {strategy_config.name}")
        
        # 4. 确定股票池
        if stock_pool is None:
            stock_pool = strategy_config.stock_pool or []
        
        if not stock_pool:
            raise ValueError("股票池为空，无法回测")
        
        # 5. 创建回测引擎
        self.update_state(
            state="PROGRESS",
            meta={"status": "正在运行回测..."}
        )
        
        backtest_engine = BacktestEngine(initial_cash=initial_cash)
        
        # 6. 运行回测
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        
        backtest_result = backtest_engine.run_backtest(
            strategy=strategy,
            start=start_date,
            end=end_date,
            stock_pool=stock_pool
        )
        
        # 7. 分析结果
        self.update_state(
            state="PROGRESS",
            meta={"status": "正在分析回测结果..."}
        )
        
        analyzer = BacktestAnalyzer()
        analysis = analyzer.analyze(backtest_result)
        
        # 8. 更新 BacktestResult 记录
        backtest_record.strategy_name = strategy_config.name
        backtest_record.final_value = backtest_result.get("final_value")
        backtest_record.total_return = backtest_result.get("total_return")
        backtest_record.annual_return = analysis.get("metrics", {}).get("annual_return")
        backtest_record.sharpe_ratio = analysis.get("metrics", {}).get("sharpe_ratio")
        backtest_record.max_drawdown = analysis.get("metrics", {}).get("max_drawdown")
        backtest_record.win_rate = analysis.get("metrics", {}).get("win_rate")
        backtest_record.total_trades = analysis.get("metrics", {}).get("total_trades", 0)
        backtest_record.equity_curve = backtest_result.get("equity_curve")
        backtest_record.trades = backtest_result.get("trades")
        backtest_record.metrics = analysis.get("metrics")
        backtest_record.status = "completed"
        backtest_record.completed_at = datetime.now()
        
        db.commit()
        
        logger.info(f"[{task_id}] ✓ 回测完成: ID={backtest_record.id}, 收益率={backtest_record.total_return:.2%}")
        
        return {
            "backtest_id": backtest_record.id,
            "strategy_name": strategy_config.name,
            "total_return": backtest_record.total_return,
            "sharpe_ratio": backtest_record.sharpe_ratio,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"[{task_id}] 回测失败: {e}")
        
        # 更新记录状态为失败
        if 'backtest_record' in locals():
            backtest_record.status = "failed"
            backtest_record.error_message = str(e)
            db.commit()
        
        # 重新抛出异常（让 Celery 标记为失败）
        raise
        
    finally:
        db.close()
