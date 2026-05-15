"""
配置管理模块
使用 Pydantic Settings 管理应用配置
支持从 .env 文件加载配置
"""
from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "A股量化交易选股系统"
    debug: bool = True
    
    # 数据源配置
    data_provider: str = "tushare"  # 数据源类型: tushare 或 akshare
    tushare_token: str = ""  # Tushare API Token
    akshare_enable: bool = True  # 是否启用 AKShare
    
    # PostgreSQL 配置
    postgres_server: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "quant_user"
    postgres_password: str = "quant_password"
    postgres_db: str = "quant_db"

    # 支持 SQLite 覆盖（验证用）
    database_url_override: Optional[str] = None

    @property
    def database_url(self) -> str:
        """构造数据库连接 URL，支持 SQLite 覆盖"""
        if self.database_url_override:
            return self.database_url_override
        password = quote_plus(self.postgres_password)
        return f"postgresql://{self.postgres_user}:{password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
    
    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Qlib 配置
    qlib_data_path: str = "./data/qlib_data"
    
    # API 配置
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 全局配置实例（单例模式）
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
