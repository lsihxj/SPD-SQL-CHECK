"""
SQL检查工具 - FastAPI应用入口
"""
import uvicorn
import yaml
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import init_database, get_db_manager
from app.utils.encryption import init_encryption_service


# 加载配置
def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    config = load_config()
    
    # 初始化加密服务
    encryption_key = config['security']['encryption_key']
    init_encryption_service(encryption_key)
    
    # 初始化数据库
    try:
        db_config = config['database']
        database_url = f"postgresql+psycopg2://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?client_encoding=utf8"
        init_database(database_url, db_config['pool_size'], db_config['max_overflow'])
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        print("提示: 请确保PostgreSQL正在运行，并且已创建数据库 'SPDSQLCheck'")
        print("创建数据库命令: CREATE DATABASE SPDSQLCheck;")
    
    print("✅ SQL检查工具启动成功")
    print(f"📝 API文档: http://localhost:{config['server']['port']}/docs")
    
    yield
    
    # 关闭时执行
    db_manager = get_db_manager()
    db_manager.close()
    print("👋 SQL检查工具已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="SQL检查工具",
    description="基于AI的PostgreSQL SQL语句检查工具",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
config = load_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors']['allow_origins'],
    allow_credentials=config['cors']['allow_credentials'],
    allow_methods=config['cors']['allow_methods'],
    allow_headers=config['cors']['allow_headers'],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "SQL检查工具API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册路由
from app.api.config import router as config_router
from app.api.check import router as check_router
from app.api.history import router as history_router
from app.api.export import router as export_router

app.include_router(config_router, prefix="/api/config", tags=["配置管理"])
app.include_router(check_router, prefix="/api/check", tags=["SQL检查"])
app.include_router(history_router, prefix="/api/history", tags=["历史记录"])
app.include_router(export_router, prefix="/api/export", tags=["导出功能"])


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "main:app",
        host=config['server']['host'],
        port=config['server']['port'],
        reload=config['server']['reload'],
        log_level=config['server']['log_level']
    )
