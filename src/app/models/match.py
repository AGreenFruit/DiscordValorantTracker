"""Pydantic models for Valorant match data"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, Any
import logging
from utils.hash import generate_match_hash

logger = logging.getLogger(__name__)


class MatchStats(BaseModel):
    """Match statistics for a player"""
    match_id: str = Field(description="Unique hash identifier for the match")
    player_name: str
    player_tag: str
    agent: str
    game_score: str
    kills: int
    deaths: int
    assists: int
    damage_delta: int = Field(description="Damage dealt minus damage received")
    headshot_percentage: float = Field(description="Headshot percentage", ge=0, le=100)
    adr: float = Field(description="Average Damage per Round")
    acs: float = Field(description="Average Combat Score")
    team_placement: int = Field(description="Placement on team (1-5)", ge=1, le=5)
    map_name: Optional[str] = None
    match_result: Optional[str] = None

    @computed_field
    @property
    def kd_ratio(self) -> float:
        """Calculate K/D ratio"""
        return round(self.kills / self.deaths, 2) if self.deaths > 0 else float(self.kills)

    @classmethod
    def from_henrik_api(cls, response: Dict[str, Any], player_name: str, player_tag: str) -> Optional['MatchStats']:
        """
        Parse API response into MatchStats.
        """
        try:
            # Check if request was successful
            if response.get('status') != 200:
                logger.warning(f"API request failed for {player_name}#{player_tag}: status {response.get('status')}")
                return None

            # Henrik API v4 structure: response['data'] is a dict with 'data' key containing list of matches
            api_data = response.get('data', {})

            if not isinstance(api_data, dict):
                logger.error(f"Expected dict for api_data, got {type(api_data)}")
                return None

            matches = api_data.get('data', [])

            if not matches or not isinstance(matches, list):
                logger.warning(f"No matches found for {player_name}#{player_tag}")
                return None

            # Get the first (most recent) match
            latest_match = matches[0]

            if not isinstance(latest_match, dict):
                logger.error(f"Expected dict for latest_match, got {type(latest_match)}")
                return None

            # Find the player's stats in the match
            player_stats = None
            players_data = latest_match.get('players', [])

            # Henrik API returns players as a list directly, not nested in 'all_players'
            if isinstance(players_data, dict):
                all_players = players_data.get('all_players', [])
            elif isinstance(players_data, list):
                all_players = players_data
            else:
                logger.error(f"Unexpected type for players_data: {type(players_data)}")
                return None

            for player in all_players:
                if (
                    player.get('name', '').lower() == player_name.lower() and
                    player.get('tag', '').lower() == player_tag.lower()
                ):
                    player_stats = player
                    break

            if not player_stats:
                logger.warning(f"Could not find stats for {player_name}#{player_tag} in match data")
                return None

            # Extract stats
            stats = player_stats.get('stats', {})
            metadata = latest_match.get('metadata', {})
            teams = latest_match.get('teams', [])

            # Calculate team placement based on score
            team_id = player_stats.get('team_id', '')
            team_players = [p for p in all_players if p.get('team_id') == team_id]
            sorted_team = sorted(
                team_players,
                key=lambda p: p.get('stats', {}).get('score', 0) if isinstance(p.get('stats'), dict) else 0,
                reverse=True)
            team_placement = next((
                i + 1 for i,
                p in enumerate(sorted_team) if p.get('name', '').lower() == player_name.lower() and
                p.get('tag', '').lower() == player_tag.lower()), 5)

            # Get team's rounds won/lost
            player_team = next((t for t in teams if t.get('team_id') == team_id), {})
            rounds_info = player_team.get('rounds', {})
            rounds_won = rounds_info.get('won', 0)
            rounds_lost = rounds_info.get('lost', 0)
            total_rounds = rounds_won + rounds_lost

            # Extract damage stats
            damage_stats = stats.get('damage', {})
            damage_dealt = damage_stats.get('dealt', 0) if isinstance(damage_stats, dict) else 0
            damage_received = damage_stats.get('received', 0) if isinstance(damage_stats, dict) else 0

            # Calculate headshot percentage
            headshots = stats.get('headshots', 0)
            bodyshots = stats.get('bodyshots', 0)
            legshots = stats.get('legshots', 0)
            total_shots = headshots + bodyshots + legshots
            headshot_pct = (headshots / total_shots * 100) if total_shots > 0 else 0

            # Get map name
            map_info = metadata.get('map', {})
            map_name = map_info.get('name', 'Unknown') if isinstance(map_info, dict) else 'Unknown'

            # Generate unique match_id hash from match_id + player
            # This creates a unique identifier for each player's performance in a specific match
            api_match_id = metadata.get('match_id', '')
            match_id = generate_match_hash(api_match_id, player_name, player_tag)

            # Build MatchStats object
            return cls(
                match_id=match_id,
                player_name=player_name,
                player_tag=player_tag,
                agent=player_stats.get('agent', {}).get('name', 'Unknown'),
                game_score=f"{rounds_won}-{rounds_lost}",
                kills=int(stats.get('kills', 0)),
                deaths=int(stats.get('deaths', 1)),
                assists=int(stats.get('assists', 0)),
                damage_delta=int(damage_dealt - damage_received),
                headshot_percentage=round(headshot_pct, 1),
                adr=round(damage_dealt / max(total_rounds, 1), 1),
                acs=round(stats.get('score', 0) / max(total_rounds, 1), 1),
                team_placement=team_placement,
                map_name=map_name,
                match_result="Victory" if player_team.get('won', False) else "Defeat"
            )

        except Exception as e:
            logger.error(f"Error parsing Henrik API response for {player_name}#{player_tag}: {e}")
            return None

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "PlayerName",
                "player_tag": "PEPE",
                "agent": "Jett",
                "game_score": "13-11",
                "kills": 25,
                "deaths": 15,
                "assists": 5,
                "damage_delta": 1500,
                "headshot_percentage": 25.5,
                "adr": 180.5,
                "acs": 275.3,
                "team_placement": 1,
                "map_name": "Ascent",
                "match_result": "Victory"
            }
        }
