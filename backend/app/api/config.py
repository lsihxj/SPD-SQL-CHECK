"""
配置管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db_session
from app.models.database import AIProvider, AIModel, ERPDatabaseConfig
from app.utils.encryption import get_encryption_service

router = APIRouter()


# Pydantic模型
class AIProviderCreate(BaseModel):
    provider_name: str
    provider_display_name: str
    api_endpoint: str
    api_key: str
    is_active: bool = True


class AIProviderUpdate(BaseModel):
    provider_display_name: str | None = None
    api_endpoint: str | None = None
    api_key: str | None = None
    is_active: bool | None = None


class AIModelCreate(BaseModel):
    provider_id: int
    model_name: str
    model_display_name: str
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    max_tokens: int = 4000
    temperature: float = 0.7
    is_default: bool = False
    is_active: bool = True


class AIModelUpdate(BaseModel):
    model_display_name: str | None = None
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class ERPDatabaseConfigCreate(BaseModel):
    config_name: str
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str
    sql_query_for_sqls: str
    is_active: bool = True


class ERPDatabaseConfigUpdate(BaseModel):
    config_name: str | None = None
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    username: str | None = None
    password: str | None = None
    sql_query_for_sqls: str | None = None
    is_active: bool | None = None


# AI厂家配置API
@router.get("/providers")
async def list_providers(db: Session = Depends(get_db_session)):
    """获取AI厂家列表"""
    providers = db.query(AIProvider).all()
    return [provider.to_dict() for provider in providers]


@router.post("/providers")
async def create_provider(
    provider: AIProviderCreate,
    db: Session = Depends(get_db_session)
):
    """创建AI厂家配置"""
    encryption = get_encryption_service()
    
    # 加密API密钥
    encrypted_api_key = encryption.encrypt(provider.api_key)
    
    db_provider = AIProvider(
        provider_name=provider.provider_name,
        provider_display_name=provider.provider_display_name,
        api_endpoint=provider.api_endpoint,
        api_key=encrypted_api_key,
        is_active=provider.is_active
    )
    
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    
    return db_provider.to_dict()


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: int,
    provider: AIProviderUpdate,
    db: Session = Depends(get_db_session)
):
    """更新AI厂家配置"""
    db_provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    encryption = get_encryption_service()
    
    if provider.provider_display_name is not None:
        db_provider.provider_display_name = provider.provider_display_name
    if provider.api_endpoint is not None:
        db_provider.api_endpoint = provider.api_endpoint
    if provider.api_key is not None:
        db_provider.api_key = encryption.encrypt(provider.api_key)
    if provider.is_active is not None:
        db_provider.is_active = provider.is_active
    
    db.commit()
    db.refresh(db_provider)
    
    return db_provider.to_dict()


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db_session)):
    """删除AI厂家配置"""
    db_provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db.delete(db_provider)
    db.commit()
    
    return {"message": "Provider deleted successfully"}


# AI模型配置API
@router.get("/models")
async def list_models(
    provider_id: int | None = None,
    db: Session = Depends(get_db_session)
):
    """获取AI模型列表"""
    query = db.query(AIModel)
    
    if provider_id:
        query = query.filter(AIModel.provider_id == provider_id)
    
    models = query.all()
    return [model.to_dict() for model in models]


@router.post("/models")
async def create_model(
    model: AIModelCreate,
    db: Session = Depends(get_db_session)
):
    """创建AI模型配置"""
    db_model = AIModel(
        provider_id=model.provider_id,
        model_name=model.model_name,
        model_display_name=model.model_display_name,
        system_prompt=model.system_prompt,
        user_prompt_template=model.user_prompt_template,
        max_tokens=model.max_tokens,
        temperature=model.temperature,
        is_default=model.is_default,
        is_active=model.is_active
    )
    
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model.to_dict()


@router.put("/models/{model_id}")
async def update_model(
    model_id: int,
    model: AIModelUpdate,
    db: Session = Depends(get_db_session)
):
    """更新AI模型配置"""
    db_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if model.model_display_name is not None:
        db_model.model_display_name = model.model_display_name
    if model.system_prompt is not None:
        db_model.system_prompt = model.system_prompt
    if model.user_prompt_template is not None:
        db_model.user_prompt_template = model.user_prompt_template
    if model.max_tokens is not None:
        db_model.max_tokens = model.max_tokens
    if model.temperature is not None:
        db_model.temperature = model.temperature
    if model.is_default is not None:
        db_model.is_default = model.is_default
    if model.is_active is not None:
        db_model.is_active = model.is_active
    
    db.commit()
    db.refresh(db_model)
    
    return db_model.to_dict()


@router.delete("/models/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db_session)):
    """删除AI模型配置"""
    db_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db.delete(db_model)
    db.commit()
    
    return {"message": "Model deleted successfully"}


# ERP数据库配置API
@router.get("/erp-databases")
async def list_erp_databases(db: Session = Depends(get_db_session)):
    """获取ERP数据库配置列表"""
    configs = db.query(ERPDatabaseConfig).all()
    return [config.to_dict() for config in configs]


@router.post("/erp-databases")
async def create_erp_database(
    config: ERPDatabaseConfigCreate,
    db: Session = Depends(get_db_session)
):
    """创建ERP数据库配置"""
    encryption = get_encryption_service()
    
    # 加密密码
    encrypted_password = encryption.encrypt(config.password)
    
    db_config = ERPDatabaseConfig(
        config_name=config.config_name,
        host=config.host,
        port=config.port,
        database_name=config.database_name,
        username=config.username,
        password=encrypted_password,
        sql_query_for_sqls=config.sql_query_for_sqls,
        is_active=config.is_active
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config.to_dict()


@router.put("/erp-databases/{config_id}")
async def update_erp_database(
    config_id: int,
    config: ERPDatabaseConfigUpdate,
    db: Session = Depends(get_db_session)
):
    """更新ERP数据库配置"""
    db_config = db.query(ERPDatabaseConfig).filter(ERPDatabaseConfig.id == config_id).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    encryption = get_encryption_service()
    
    if config.config_name is not None:
        db_config.config_name = config.config_name
    if config.host is not None:
        db_config.host = config.host
    if config.port is not None:
        db_config.port = config.port
    if config.database_name is not None:
        db_config.database_name = config.database_name
    if config.username is not None:
        db_config.username = config.username
    if config.password is not None:
        db_config.password = encryption.encrypt(config.password)
    if config.sql_query_for_sqls is not None:
        db_config.sql_query_for_sqls = config.sql_query_for_sqls
    if config.is_active is not None:
        db_config.is_active = config.is_active
    
    db.commit()
    db.refresh(db_config)
    
    return db_config.to_dict()


@router.delete("/erp-databases/{config_id}")
async def delete_erp_database(config_id: int, db: Session = Depends(get_db_session)):
    """删除ERP数据库配置"""
    db_config = db.query(ERPDatabaseConfig).filter(ERPDatabaseConfig.id == config_id).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    db.delete(db_config)
    db.commit()
    
    return {"message": "Config deleted successfully"}


@router.get("/erp-databases/{config_id}/sqls")
async def get_erp_sqls(
    config_id: int,
    db: Session = Depends(get_db_session)
):
    """从ERP数据库获取SQL语句列表"""
    from app.core.database import get_or_create_erp_connection
    
    # 获取ERP数据库配置
    db_config = db.query(ERPDatabaseConfig).filter(ERPDatabaseConfig.id == config_id).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    encryption = get_encryption_service()
    
    try:
        # 解密密码
        password = encryption.decrypt(db_config.password)
        
        # 创建数据库连接
        erp_conn = get_or_create_erp_connection(
            config_id=config_id,
            host=db_config.host,
            port=db_config.port,
            database=db_config.database_name,
            username=db_config.username,
            password=password
        )
        
        # 测试连接
        if not erp_conn.test_connection():
            raise HTTPException(status_code=500, detail="Failed to connect to ERP database")
        
        # 执行查询获取SQL列表
        sql_list = []
        with erp_conn.get_cursor() as cursor:
            cursor.execute(db_config.sql_query_for_sqls)
            rows = cursor.fetchall()
            
            for row in rows:
                # 假设查询返回两列: id, sql_content
                if len(row) >= 2:
                    sql_list.append({
                        'id': row[0],
                        'sql': row[1]
                    })
        
        return {
            'total': len(sql_list),
            'sqls': sql_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SQL list: {str(e)}")


@router.post("/erp-databases/{config_id}/test")
async def test_erp_connection(
    config_id: int,
    db: Session = Depends(get_db_session)
):
    """测试ERP数据库连接"""
    from app.core.database import get_or_create_erp_connection
    
    db_config = db.query(ERPDatabaseConfig).filter(ERPDatabaseConfig.id == config_id).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    encryption = get_encryption_service()
    
    try:
        password = encryption.decrypt(db_config.password)
        
        erp_conn = get_or_create_erp_connection(
            config_id=config_id,
            host=db_config.host,
            port=db_config.port,
            database=db_config.database_name,
            username=db_config.username,
            password=password
        )
        
        if erp_conn.test_connection():
            return {"status": "success", "message": "连接成功"}
        else:
            raise HTTPException(status_code=500, detail="Connection test failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")
