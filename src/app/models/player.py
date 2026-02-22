"""Pydantic models for Valorant player data"""
from pydantic import BaseModel, Field, computed_field
from utils.hash import generate_player_hash


class Player(BaseModel):
    """Player model for database operations"""
    username: str = Field(description="Valorant username")
    tag: str = Field(description="Valorant tag (without #)")
    discord_id: int = Field(description="Discord user ID")

    @computed_field
    @property
    def hash(self) -> str:
        """Generate unique hash for the player"""
        return generate_player_hash(self.username, self.tag, self.discord_id)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "PlayerName",
                "tag": "PEPE",
                "discord_id": 123456789012345678,
                "hash": "a1b2c3d4e5f6g7h8"
            }
        }
