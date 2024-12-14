"""Example user model."""

from sqlalchemy import Column, String, BigInteger, Boolean
from ..base import BaseModel


class User(BaseModel):
    """Discord user model."""

    __tablename__ = "users"

    discord_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User(discord_id={self.discord_id}, name='{self.name}')>"
