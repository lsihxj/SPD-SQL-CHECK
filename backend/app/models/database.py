"""
SQLAlchemy数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, DECIMAL, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AIProvider(Base):
    """AI厂家配置表"""
    __tablename__ = 'ai_providers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(50), nullable=False, unique=True, comment='厂家名称')
    provider_display_name = Column(String(100), nullable=False, comment='显示名称')
    api_endpoint = Column(String(500), nullable=False, comment='API端点地址')
    api_key = Column(String(500), nullable=False, comment='API密钥（加密存储）')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='更新时间')

    # 关系
    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'provider_name': self.provider_name,
            'provider_display_name': self.provider_display_name,
            'api_endpoint': self.api_endpoint,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AIModel(Base):
    """AI模型配置表"""
    __tablename__ = 'ai_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey('ai_providers.id', ondelete='CASCADE'), nullable=False)
    model_name = Column(String(100), nullable=False, comment='模型名称')
    model_display_name = Column(String(100), nullable=False, comment='显示名称')
    system_prompt = Column(Text, comment='系统提示词')
    user_prompt_template = Column(Text, comment='用户提示词模板')
    max_tokens = Column(Integer, default=4000, comment='最大令牌数')
    temperature = Column(DECIMAL(3, 2), default=0.7, comment='温度参数')
    is_default = Column(Boolean, default=False, comment='是否默认模型')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='更新时间')

    # 关系
    provider = relationship("AIProvider", back_populates="models")
    check_records = relationship("SQLCheckRecord", back_populates="ai_model")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'model_name': self.model_name,
            'model_display_name': self.model_display_name,
            'system_prompt': self.system_prompt,
            'user_prompt_template': self.user_prompt_template,
            'max_tokens': self.max_tokens,
            'temperature': float(self.temperature) if self.temperature else None,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ERPDatabaseConfig(Base):
    """ERP数据库配置表"""
    __tablename__ = 'erp_database_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(100), nullable=False, comment='配置名称')
    host = Column(String(200), nullable=False, comment='数据库主机')
    port = Column(Integer, nullable=False, default=5432, comment='端口号')
    database_name = Column(String(100), nullable=False, comment='数据库名')
    username = Column(String(100), nullable=False, comment='用户名')
    password = Column(String(500), nullable=False, comment='密码（加密存储）')
    sql_query_for_sqls = Column(Text, nullable=False, comment='获取SQL语句的查询语句')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='更新时间')

    def to_dict(self):
        """转换为字典（不包含密码）"""
        return {
            'id': self.id,
            'config_name': self.config_name,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'sql_query_for_sqls': self.sql_query_for_sqls,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SQLCheckRecord(Base):
    """SQL检查记录表"""
    __tablename__ = 'sql_check_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), comment='批次ID')
    original_sql = Column(Text, nullable=False, comment='原始SQL语句')
    sql_hash = Column(String(64), comment='SQL的哈希值')
    check_type = Column(String(20), nullable=False, comment='检查类型（single/batch/all）')
    ai_model_id = Column(Integer, ForeignKey('ai_models.id', ondelete='SET NULL'))
    ai_check_result = Column(Text, comment='AI检查结果')
    explain_result = Column(Text, comment='EXPLAIN执行计划结果')
    performance_metrics = Column(JSONB, comment='性能指标（JSON格式）')
    check_status = Column(String(20), nullable=False, comment='检查状态（pending/success/failed）')
    error_message = Column(Text, comment='错误信息')
    check_duration = Column(Integer, comment='检查耗时（毫秒）')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    checked_at = Column(TIMESTAMP, comment='检查完成时间')

    # 关系
    ai_model = relationship("AIModel", back_populates="check_records")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'original_sql': self.original_sql,
            'sql_hash': self.sql_hash,
            'check_type': self.check_type,
            'ai_model_id': self.ai_model_id,
            'ai_check_result': self.ai_check_result,
            'explain_result': self.explain_result,
            'performance_metrics': self.performance_metrics,
            'check_status': self.check_status,
            'error_message': self.error_message,
            'check_duration': self.check_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None
        }


class CheckSummary(Base):
    """检查结果汇总表"""
    __tablename__ = 'check_summary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), unique=True, nullable=False, comment='批次ID')
    total_count = Column(Integer, nullable=False, comment='总SQL数量')
    success_count = Column(Integer, default=0, comment='成功数量')
    failed_count = Column(Integer, default=0, comment='失败数量')
    warning_count = Column(Integer, default=0, comment='警告数量')
    start_time = Column(TIMESTAMP, nullable=False, comment='开始时间')
    end_time = Column(TIMESTAMP, comment='结束时间')
    total_duration = Column(Integer, comment='总耗时（秒）')
    created_by = Column(String(100), comment='创建人')
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'warning_count': self.warning_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration': self.total_duration,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
