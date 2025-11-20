"""
SQL检查API路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db_session
from app.services.sql_checker import SQLCheckEngine

router = APIRouter()


# Pydantic模型
class SQLCheckRequest(BaseModel):
    sql_statement: str
    model_id: int
    explain_result: str | None = None
    erp_config_id: int | None = None  # 用于自动执行EXPLAIN


class BatchSQLCheckRequest(BaseModel):
    sql_statements: List[dict]  # [{"sql": "...", "explain_result": "..."}]
    model_id: int
    erp_config_id: int | None = None  # 用于自动执行EXPLAIN


class CheckAllFromERPRequest(BaseModel):
    erp_config_id: int
    model_id: int
    auto_explain: bool = True


@router.post("/single")
async def check_single_sql(
    request: SQLCheckRequest,
    db: Session = Depends(get_db_session)
):
    """单个SQL检查"""
    engine = SQLCheckEngine(db)
    
    result = await engine.check_single(
        sql_statement=request.sql_statement,
        model_id=request.model_id,
        explain_result=request.explain_result,
        erp_config_id=request.erp_config_id
    )
    
    return result.to_dict()


@router.post("/single/stream")
async def check_single_sql_stream(
    request: SQLCheckRequest,
    db: Session = Depends(get_db_session)
):
    """单个SQL检查（流式输出）"""
    engine = SQLCheckEngine(db)
    
    async def generate():
        async for chunk in engine.check_single_stream(
            sql_statement=request.sql_statement,
            model_id=request.model_id,
            explain_result=request.explain_result,
            erp_config_id=request.erp_config_id
        ):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/batch")
async def check_batch_sqls(
    request: BatchSQLCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """批量SQL检查"""
    engine = SQLCheckEngine(db)
    
    # 启动批量检查（异步执行）
    result = await engine.check_batch(
        sql_statements=request.sql_statements,
        model_id=request.model_id,
        erp_config_id=request.erp_config_id
    )
    
    return result


@router.get("/progress/{batch_id}")
async def get_check_progress(
    batch_id: str,
    db: Session = Depends(get_db_session)
):
    """获取批量检查进度"""
    engine = SQLCheckEngine(db)
    
    try:
        progress = engine.get_batch_progress(batch_id)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/all")
async def check_all_from_erp(
    request: CheckAllFromERPRequest,
    db: Session = Depends(get_db_session)
):
    """从ERP数据库获取所有SQL并批量检查"""
    engine = SQLCheckEngine(db)
    
    try:
        result = await engine.check_all_from_erp(
            erp_config_id=request.erp_config_id,
            model_id=request.model_id,
            auto_explain=request.auto_explain
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
