from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import asyncio

from app.api.dependencies import get_session, get_current_user, require_engineer, require_viewer
from app.models.user import User
from app.schemas.report import ReportRequest, ReportResponse
from app.services import report_service
from app.core.config import get_settings

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    payload: ReportRequest,
    session: AsyncSession = Depends(get_session),
    # Allow any authenticated user (viewer/engineer/admin) to generate reports
    current_user: User = Depends(require_viewer),
):
    """Generate a report (optimized for fast CSV generation)"""
    try:
        # For CSV, use optimized fast path
        if payload.format == "csv":
            return await report_service.generate_report_fast(session, payload)
        else:
            return await report_service.generate_report(session, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/download/{filename:path}")
async def download_report_by_filename(
    filename: str,
    session: AsyncSession = Depends(get_session),
    # Same permission as generate: any authenticated user
    current_user: User = Depends(require_viewer),
):
    """Download a report by filename (for compatibility with static file serving)"""
    # Security: Only allow files from reports directory
    report_path = settings.reports_dir / filename
    # Prevent directory traversal
    if not str(report_path.resolve()).startswith(str(settings.reports_dir.resolve())):
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
    
    # Determine content type and headers
    content_type = "application/octet-stream"
    disposition = f'attachment; filename="{filename}"'
    
    if filename.endswith(".csv"):
        content_type = "text/csv; charset=utf-8"
    elif filename.endswith(".pdf"):
        content_type = "application/pdf"
        # For PDFs, try inline first, fallback to attachment
        disposition = f'inline; filename="{filename}"'
    elif filename.endswith(".xlsx"):
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Verify file is readable
    if not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report file is not accessible")
    
    return FileResponse(
        report_path,
        media_type=content_type,
        filename=filename,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
):
    """Download a generated report"""
    # In a real implementation, you'd look up the report by ID
    # For now, we'll check if the file exists in the reports directory
    report_path = settings.reports_dir / f"{report_id}.pdf"
    if not report_path.exists():
        # Try other formats
        for ext in ["csv", "xlsx", "json"]:
            report_path = settings.reports_dir / f"{report_id}.{ext}"
            if report_path.exists():
                break
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if report_path.suffix == ".pdf":
        content_type = "application/pdf"
    elif report_path.suffix == ".csv":
        content_type = "text/csv; charset=utf-8"
    elif report_path.suffix == ".xlsx":
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return FileResponse(
        report_path,
        media_type=content_type,
        filename=report_path.name,
        headers={
            "Content-Disposition": f'attachment; filename="{report_path.name}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
