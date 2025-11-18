"""Hash utility functions for generating unique identifiers"""
import hashlib


def generate_hash(identifier: str, length: int = 16) -> str:
    """
    Generate a SHA256 hash from an identifier string.
    """
    return hashlib.sha256(identifier.encode()).hexdigest()[:length]


def generate_player_hash(username: str, tag: str, discord_id: int) -> str:
    """
    Generate a unique hash for a player based on username and tag.
    """
    identifier = f"{username}#{tag}:{discord_id}"
    return generate_hash(identifier, length=16)


def generate_match_hash(match_id: str, username: str, tag: str) -> str:
    """
    Generate a unique hash for a player's match performance.
    """
    identifier = f"{match_id}:{username}#{tag}"
    return generate_hash(identifier, length=16)
