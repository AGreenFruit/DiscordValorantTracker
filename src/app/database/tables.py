"""Database table abstractions for clean ORM-like operations"""
import psycopg2
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


def create_tables(conn, cursor) -> None:
    """Create tables if they don't exist"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            username VARCHAR(255) NOT NULL,
            tag VARCHAR(255) NOT NULL,
            discord_id BIGINT NOT NULL,
            hash VARCHAR(16) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_stats (
            match_id VARCHAR(16) PRIMARY KEY,
            player_name VARCHAR(255) NOT NULL,
            player_tag VARCHAR(255) NOT NULL,
            agent VARCHAR(100),
            game_score VARCHAR(20),
            kills INT,
            deaths INT,
            assists INT,
            kd_ratio FLOAT,
            damage_delta INT,
            headshot_percentage FLOAT,
            adr FLOAT,
            acs FLOAT,
            team_placement INT,
            map_name VARCHAR(100),
            match_result VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    logger.info("Database tables verified/created")


class Table:
    """Base table class for database operations"""

    def __init__(self, conn, cursor, table_name: str):
        self.conn = conn
        self.cursor = cursor
        self.table_name = table_name

    def insert(self, model: BaseModel, on_conflict: Optional[str] = None) -> bool:
        """
        Insert a Pydantic model into the table.
        """
        try:
            # Get model data as dict, including computed fields
            data = model.model_dump()

            # Build INSERT query
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = tuple(data.values())

            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

            if on_conflict:
                query += f" ON CONFLICT {on_conflict}"

            self.cursor.execute(query, values)
            self.conn.commit()

            return True

        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.debug(f"Integrity error inserting into {self.table_name}: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting into {self.table_name}: {e}")
            raise

    def find_one(self, **conditions) -> Optional[Dict[str, Any]]:
        """
        Find a single row matching conditions.
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
        values = tuple(conditions.values())

        query = f"SELECT * FROM {self.table_name} WHERE {where_clause} LIMIT 1"

        self.cursor.execute(query, values)
        result = self.cursor.fetchone()

        if result:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, result))

        return None


class PlayersTable(Table):
    """Players table with custom methods"""

    def __init__(self, conn, cursor):
        super().__init__(conn, cursor, "players")

    def insert(self, model: BaseModel) -> bool:
        """
        Insert a player into the database.
        Returns True if player was inserted, False if already exists.
        """
        try:
            # Get model data as dict, including computed fields
            data = model.model_dump()

            # Build INSERT query with RETURNING clause to check if row was inserted
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = tuple(data.values())

            query = f"""
                INSERT INTO {self.table_name} ({columns}) 
                VALUES ({placeholders})
                ON CONFLICT (hash) DO NOTHING
                RETURNING hash
            """

            self.cursor.execute(query, values)
            result = self.cursor.fetchone()
            self.conn.commit()

            # If result is None, the row already existed (conflict occurred)
            return result is not None

        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.debug(f"Integrity error inserting into {self.table_name}: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting into {self.table_name}: {e}")
            raise

    def delete(self, username: str, tag: str, discord_id: int) -> bool:
        """
        Delete a player from tracking.
        Returns True if a player was deleted, False if not found.
        """
        try:
            self.cursor.execute(
                f"DELETE FROM {self.table_name} WHERE username = %s AND tag = %s AND discord_id = %s RETURNING hash",
                (username, tag, discord_id)
            )
            result = self.cursor.fetchone()
            self.conn.commit()
            return result is not None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error deleting from {self.table_name}: {e}")
            raise


class MatchStatsTable(Table):
    """Match stats table with custom methods"""

    def __init__(self, conn, cursor):
        super().__init__(conn, cursor, "match_stats")

    def insert(self, model: BaseModel) -> List[int]:
        """
        Insert a match stat and return list of discord_ids tracking this player.
        Returns empty list if match already existed.
        """
        # Try to insert the match
        success = super().insert(model)

        if success:
            self.cursor.execute(
                "SELECT discord_id FROM players WHERE username = %s AND tag = %s",
                (model.player_name, model.player_tag)
            )
            results = self.cursor.fetchall()

            discord_ids = [row[0] for row in results if row[0]]
            if discord_ids:
                logger.info(f"New match recorded for {model.player_name}#{model.player_tag}, notifying {len(discord_ids)} user(s)")
            return discord_ids

        return []
