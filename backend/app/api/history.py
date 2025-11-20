"""
历史记录API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db_session
from app.models.database import SQLCheckRecord, CheckSummary

router = APIRouter()


@router.get("/records")
async def list_check_records(
    batch_id: Optional[str] = None,
    check_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """获取检查记录列表"""
    query = db.query(SQLCheckRecord)
    
    # 应用过滤条件
    if batch_id:
        query = query.filter(SQLCheckRecord.batch_id == batch_id)
    
    if check_status:
        query = query.filter(SQLCheckRecord.check_status == check_status)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(SQLCheckRecord.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(SQLCheckRecord.created_at <= end_dt)
    
    # 排序和分页
    records = query.order_by(SQLCheckRecord.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        'total': total,
        'records': [record.to_dict() for record in records]
    }


@router.get("/records/{record_id}")
async def get_check_record(
    record_id: int,
    db: Session = Depends(get_db_session)
):
    """获取单个检查记录详情"""
    record = db.query(SQLCheckRecord).filter(SQLCheckRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return record.to_dict()


@router.get("/summary")
async def list_check_summaries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db_session)
):
    """获取检查汇总列表"""
    query = db.query(CheckSummary)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(CheckSummary.start_time >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(CheckSummary.start_time <= end_dt)
    
    summaries = query.order_by(CheckSummary.start_time.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        'total': total,
        'summaries': [summary.to_dict() for summary in summaries]
    }


@router.get("/summary/{batch_id}")
async def get_check_summary(
    batch_id: str,
    db: Session = Depends(get_db_session)
):
    """获取批次汇总详情"""
    summary = db.query(CheckSummary).filter(CheckSummary.batch_id == batch_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # 获取该批次的所有记录
    records = db.query(SQLCheckRecord).filter(SQLCheckRecord.batch_id == batch_id).all()
    
    return {
        'summary': summary.to_dict(),
        'records': [record.to_dict() for record in records]
    }
