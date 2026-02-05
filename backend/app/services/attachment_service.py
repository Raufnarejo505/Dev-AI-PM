import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.attachment import Attachment

settings = get_settings()
attachments_dir = settings.reports_dir / "attachments"
attachments_dir.mkdir(parents=True, exist_ok=True)


async def get_attachment(session: AsyncSession, attachment_id: UUID) -> Optional[Attachment]:
    """Get an attachment by ID"""
    result = await session.execute(select(Attachment).where(Attachment.id == attachment_id))
    return result.scalar_one_or_none()


async def create_attachment(
    session: AsyncSession,
    file: UploadFile,
    resource_type: str,
    resource_id: Optional[str] = None,
    uploaded_by: Optional[str] = None,
) -> Attachment:
    """Create an attachment from uploaded file"""
    # Generate unique filename
    file_ext = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"{UUID()}{file_ext}"
    file_path = attachments_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create database record
    attachment = Attachment(
        filename=file.filename or "unknown",
        file_path=str(file_path),
        content_type=file.content_type,
        file_size=len(content),
        resource_type=resource_type,
        resource_id=resource_id,
        uploaded_by=uploaded_by,
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def delete_attachment(session: AsyncSession, attachment: Attachment) -> None:
    """Delete attachment file and record"""
    # Delete file
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    # Delete record
    await session.delete(attachment)
    await session.commit()

