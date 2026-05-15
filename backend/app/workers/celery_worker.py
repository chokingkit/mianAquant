"""
Celery Worker 启动脚本
用于启动 Celery Worker 进程

使用方法:
    python -m app.workers.celery_worker
    或
    celery -A app.workers.celery_worker worker --loglevel=info -c 4
"""
import sys
import logging
from loguru import logger

# 必须导入 celery_app，否则 Celery 无法发现任务
from app.tasks.celery_app import celery_app

# 导入所有任务模块（确保任务被注册）
import app.tasks.backtest_tasks


def main():
    """启动 Celery Worker"""
    import celery.bin.worker
    
    worker = celery.bin.worker.worker(app=celery_app)
    
    # Worker 参数
    worker.run(
        loglevel="INFO",
        concurrency=4,  # 并发 worker 数
        max_tasks_per_child=1000,
        prefetch_multiplier=1,
    )


if __name__ == "__main__":
    main()
