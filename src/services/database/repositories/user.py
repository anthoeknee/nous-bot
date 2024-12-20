from typing import Optional
from sqlalchemy import select
from .base import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()
