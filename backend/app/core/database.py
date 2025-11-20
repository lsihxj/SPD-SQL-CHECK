"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import psycopg2
from psycopg2.pool import SimpleConnectionPool

from app.models.database import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        """
        初始化数据库管理器
        
        Args:
            database_url: 数据库连接URL
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
        """
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # 自动检测失效连接
            echo=False
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（使用上下文管理器）
        
        Yields:
            Session对象
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()


class ERPDatabaseConnection:
    """ERP数据库连接管理器"""
    
    def __init__(self, host: str, port: int, database: str, username: str, password: str, 
                 min_conn: int = 1, max_conn: int = 10):
        """
        初始化ERP数据库连接
        
        Args:
            host: 数据库主机
            port: 端口号
            database: 数据库名
            username: 用户名
            password: 密码
            min_conn: 最小连接数
            max_conn: 最大连接数
        """
        self.pool = SimpleConnectionPool(
            min_conn,
            max_conn,
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（使用上下文管理器）
        
        Yields:
            psycopg2连接对象
        """
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self):
        """
        获取数据库游标（使用上下文管理器）
        
        Yields:
            psycopg2游标对象
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.closeall()
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            连接是否成功
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False


# 全局数据库管理器实例
_db_manager: DatabaseManager | None = None
_erp_db_connections: dict[int, ERPDatabaseConnection] = {}


def init_database(database_url: str, pool_size: int = 10, max_overflow: int = 20):
    """
    初始化全局数据库管理器
    
    Args:
        database_url: 数据库连接URL
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, pool_size, max_overflow)


def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例
    
    Returns:
        DatabaseManager实例
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于FastAPI依赖注入）
    
    Yields:
        Session对象
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


def get_or_create_erp_connection(config_id: int, host: str, port: int, database: str, 
                                  username: str, password: str) -> ERPDatabaseConnection:
    """
    获取或创建ERP数据库连接
    
    Args:
        config_id: 配置ID
        host: 数据库主机
        port: 端口号
        database: 数据库名
        username: 用户名
        password: 密码（已解密）
        
    Returns:
        ERPDatabaseConnection实例
    """
    if config_id not in _erp_db_connections:
        _erp_db_connections[config_id] = ERPDatabaseConnection(
            host, port, database, username, password
        )
    return _erp_db_connections[config_id]


def close_all_erp_connections():
    """关闭所有ERP数据库连接"""
    for conn in _erp_db_connections.values():
        conn.close()
    _erp_db_connections.clear()
