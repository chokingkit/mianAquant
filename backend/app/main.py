"""
FastAPI 应用入口
配置 CORS、日志、健康检查等基础功能
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.api.v1.endpoints import router as api_router
from app.data.factory import DataProviderFactory
from app.api.deps import engine as db_engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动 A股量化交易选股系统...")
    
    # 注册数据提供者（延迟导入，避免某个 provider 未安装时导致应用无法启动）
    factory = DataProviderFactory.get_instance()
    
    try:
        from app.data.providers.tushare_provider import TushareProvider
        factory.register_provider('tushare', TushareProvider)
        logger.info("✓ Tushare 提供者已注册")
    except Exception as e:
        logger.warning(f"Tushare 提供者注册失败（可能未安装 tushare）: {e}")
    
    try:
        from app.data.providers.akshare_provider import AKShareProvider
        factory.register_provider('akshare', AKShareProvider)
        logger.info("✓ AKShare 提供者已注册")
    except Exception as e:
        logger.warning(f"AKShare 提供者注册失败（可能未安装 akshare）: {e}")
    
    logger.info("✓ 数据提供者注册完成")
    
    # 根据配置创建默认数据提供者
    settings = get_settings()
    try:
        default_provider = factory.create_provider(settings.data_provider)
        logger.info(f"✓ 默认数据提供者已创建: {settings.data_provider}")
    except Exception as e:
        logger.warning(f"默认数据提供者创建失败: {e}")
    
    # 创建数据库表
    try:
        from app.api.deps import create_tables
        create_tables()
        logger.info("✓ 数据库表创建完成")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
    
    yield
    
    # 清理资源
    factory.clear_all()
    logger.info("🛑 关闭 A股量化交易选股系统...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="基于 qlib 框架的 A 股量化交易选股系统",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    register_routes(app)
    
    return app


def register_routes(app: FastAPI) -> None:
    """注册路由"""
    
    # 注册 API v1 路由
    app.include_router(api_router)
    
    @app.get("/")
    async def root(settings: Settings = Depends(get_settings)):
        """根路由 - 返回系统信息"""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "debug": settings.debug,
            "data_provider": settings.data_provider,
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "ok"}


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
