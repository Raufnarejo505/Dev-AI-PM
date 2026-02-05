from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.schemas.comment import CommentCreate


async def get_comment(session: AsyncSession, comment_id: UUID) -> Optional[Comment]:
    """Get a comment by ID"""
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    return result.scalar_one_or_none()


async def get_comments(
    session: AsyncSession,
    resource_type: str,
    resource_id: str,
) -> List[Comment]:
    """Get all comments for a resource"""
    result = await session.execute(
        select(Comment)
        .where(Comment.resource_type == resource_type, Comment.resource_id == resource_id)
        .order_by(Comment.created_at.desc())
    )
    return list(result.scalars().all())


async def create_comment(
    session: AsyncSession,
    comment_data: CommentCreate,
    user_id: str,
) -> Comment:
    """Create a new comment"""
    comment = Comment(
        resource_type=comment_data.resource_type,
        resource_id=comment_data.resource_id,
        user_id=user_id,
        content=comment_data.content,
        is_internal="true" if comment_data.is_internal else "false",
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment

