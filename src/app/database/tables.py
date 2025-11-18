"""Database table abstractions for clean ORM-like operations"""
import psycopg2
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


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
        super().__init__(conn, cursor, "valorant.players")

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


class MatchStatsTable(Table):
    """Match stats table with custom methods"""

    def __init__(self, conn, cursor):
        super().__init__(conn, cursor, "valorant.match_stats")

    def insert(self, model: BaseModel) -> Optional[int]:
        """
        Insert a match stat and return discord_id if it's a new match.
        """
        # Try to insert the match
        success = super().insert(model)

        if success:
            self.cursor.execute(
                "SELECT discord_id FROM valorant.players WHERE username = %s AND tag = %s",
                (model.player_name, model.player_tag)
            )
            result = self.cursor.fetchone()

            if result and result[0]:
                logger.info(f"New match recorded for {model.player_name}#{model.player_tag}")
                return result[0]

        return None
