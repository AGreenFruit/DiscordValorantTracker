import asyncio
from typing import Dict, Any
import logging
import psycopg2
import os
from dotenv import load_dotenv

from interfaces.job import Job

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrackerJob(Job):
    """Tracker job class that fetches player stats from Tracker.gg API for each player in the database"""

    def __init__(self, job_id: str = "tracker_job"):
        super().__init__(job_id)
        self.conn = None
        self.cursor = None

    async def setup_resources(self) -> None:
        """Setup database connection"""
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "valorant_tracker"),
            user=os.getenv("DB_USER", "danielchen"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        self.cursor = self.conn.cursor()
        logger.info("Database connection established")
        
        # Register cleanup to close connection
        self.register_cleanup(self._close_db_connection)

    def _close_db_connection(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    async def run_implementation(self) -> Dict[str, Any]:
        # Retreive list of players through DB
        self.cursor.execute("SELECT * FROM player.players")
        players = self.cursor.fetchall()
        print(players)
        # Fetch last match of eachplayer stats from Tracker.gg API
        # Put API response into Match model
        # Insert+update Match model into DB
        # Have discord bot send messages to channel if match is a new record

        return {}


if __name__ == "__main__":
    job = TrackerJob()
    result = asyncio.run(job.execute())