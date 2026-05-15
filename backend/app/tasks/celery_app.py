"""
Celery 应用配置
使用 Redis 作为 broker 和 backend
"""
from celery import Celery
from app.config import get_settings

def create_celery_app() -> Celery:
    """
    创建 Celery 应用实例
    
    Returns:
        Celery: Celery 应用实例
    """
    settings = get_settings()
    
    # 构建 Redis URL
    if settings.redis_password:
        redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    else:
        redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    
    app = Celery(
        "quant_system",
        broker=redis_url,
        backend=redis_url,
    )
    
    # Celery 配置
    app.conf.update(
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 分钟
        task_soft_time_limit=25 * 60,  # 软超时 25 分钟
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        result_expires=60 * 60 * 24 * 7,  # 结果保留 7 天
        worker_prefetch_multiplier=1,  # 每次只取一个任务（避免长时间占用）
        task_acks_late=True,  # 任务完成后再确认（防止丢失）
        worker_max_tasks_per_child=1000,  # 每个 worker 处理 1000 个任务后重启
    )
    
    return app


# 全局 Celery 应用实例
celery_app = create_celery_app()
