import asyncio
from typing import Dict, Any, List
import logging
import psycopg2
import os
from dotenv import load_dotenv

from interfaces.job import Job
from utils.http import request_many
from app.models.match import MatchStats
from app.database.tables import MatchStatsTable, create_tables

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

    def __init__(self, job_id: str = "tracker_job", notifier=None):
        super().__init__(job_id)
        self.conn = None
        self.cursor = None
        self.notifier = notifier

    async def setup_resources(self) -> None:
        """Setup database connection"""
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "valorant"),
            user=os.getenv("DB_USER", "danielchen"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        create_tables(self.conn, self.cursor)

        # Initialize table abstractions
        self.match_stats_table = MatchStatsTable(self.conn, self.cursor)

        # Register cleanup to close connection
        self.register_cleanup(self._close_db_connection)

    def _close_db_connection(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    async def fetch_player_metrics(self, players: List[tuple]) -> List[Dict[str, Any]]:
        """Fetch player metrics from Henrik's Valorant API for each player"""
        requests = []
        api_key = os.getenv("HENRIK_API_KEY")

        for player in players:
            username, tag = player
            region = 'na'
            # Try v1 endpoint which may not require auth
            url = f"https://api.henrikdev.xyz/valorant/v4/matches/{region}/pc/{username}/{tag}?mode=competitive&size=1"
            headers = {
                "Authorization": api_key,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
            requests.append(("GET", url, None, headers))

        results = await request_many(requests)

        return results

    async def run_implementation(self) -> Dict[str, Any]:
        # Retrieve list of players from DB
        self.cursor.execute("SELECT username, tag FROM players")
        players = self.cursor.fetchall()

        # Fetch match stats from API
        results = await self.fetch_player_metrics(players)

        # Parse into MatchStats models
        match_stats = []
        for response, (player_name, player_tag) in zip(results, players):
            match_stat = MatchStats.from_henrik_api(response, player_name, player_tag)
            if match_stat:
                match_stats.append(match_stat)

        # Insert matches and collect notifications for new matches
        new_matches = []
        for stats in match_stats:
            discord_user_ids = self.match_stats_table.insert(stats)
            for discord_user_id in discord_user_ids:
                new_matches.append({
                    "discord_user_id": discord_user_id,
                    "stats": stats
                })

        # Send Discord notifications for new matches
        notifications_sent = 0
        if self.notifier and new_matches:
            notifications_sent = await self.notifier.send_bulk_notifications(new_matches)
            logger.info(f"Sent {notifications_sent}/{len(new_matches)} Discord notifications")

        return {
            "players_processed": len(players),
            "matches_parsed": len(match_stats),
            "new_matches": len(new_matches),
            "notifications_sent": notifications_sent
        }


if __name__ == "__main__":
    job = TrackerJob()
    result = asyncio.run(job.execute())
    logger.info(result)
