"""
导出API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db_session
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/excel/{batch_id}")
async def export_excel(
    batch_id: str,
    db: Session = Depends(get_db_session)
):
    """导出Excel文件"""
    service = ExportService(db)
    
    try:
        excel_data = service.export_to_excel(batch_id)
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=sql_check_{batch_id}.xlsx"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{batch_id}")
async def export_pdf(
    batch_id: str,
    db: Session = Depends(get_db_session)
):
    """导出PDF文件"""
    service = ExportService(db)
    
    try:
        pdf_data = service.export_to_pdf(batch_id)
        
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=sql_check_{batch_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
