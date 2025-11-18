"""Discord notification service for sending match updates"""
import discord
import logging
from app.models.match import MatchStats

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Service for sending Discord notifications"""

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def send_match_notification(self, discord_user_id: int, stats: MatchStats) -> bool:
        """
        Send a match notification to a Discord user.

        Args:
            discord_user_id: Discord user ID to notify
            stats: MatchStats object with match data

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            user = await self.bot.fetch_user(discord_user_id)
            if not user:
                logger.warning(f"Could not find Discord user with ID {discord_user_id}")
                return False

            # Create embed for match notification
            embed = discord.Embed(
                title="🎮 New Match Detected!",
                description=f"**{stats.player_name}#{stats.player_tag}** just finished a match!",
                color=discord.Color.green() if stats.match_result == "Victory" else discord.Color.red()
            )

            # Add match details
            embed.add_field(name="Agent", value=stats.agent, inline=True)
            embed.add_field(name="Map", value=stats.map_name or "Unknown", inline=True)
            embed.add_field(name="Result", value=stats.match_result or "Unknown", inline=True)

            embed.add_field(name="Score", value=stats.game_score, inline=True)
            embed.add_field(name="K/D/A", value=f"{stats.kills}/{stats.deaths}/{stats.assists}", inline=True)
            embed.add_field(name="K/D Ratio", value=f"{stats.kd_ratio}", inline=True)

            embed.add_field(name="ACS", value=f"{stats.acs}", inline=True)
            embed.add_field(name="ADR", value=f"{stats.adr}", inline=True)
            embed.add_field(name="HS%", value=f"{stats.headshot_percentage}%", inline=True)

            embed.add_field(name="Damage Δ", value=f"{stats.damage_delta:+d}", inline=True)
            embed.add_field(name="Team Rank", value=f"#{stats.team_placement}/5", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for alignment

            embed.set_footer(text=f"Match ID: {stats.match_id}")

            # Send DM to user
            await user.send(embed=embed)
            logger.info(f"Sent match notification to Discord user {discord_user_id}")
            return True

        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {discord_user_id} - DMs may be disabled")
            return False
        except Exception as e:
            logger.error(f"Error sending notification to user {discord_user_id}: {e}")
            return False

    async def send_bulk_notifications(self, notifications: list) -> int:
        """
        Send multiple match notifications.

        Args:
            notifications: List of dicts with 'discord_user_id' and 'stats' keys

        Returns:
            Number of notifications sent successfully
        """
        sent_count = 0
        for notification in notifications:
            discord_user_id = notification.get('discord_user_id')
            stats = notification.get('stats')

            if discord_user_id and stats:
                success = await self.send_match_notification(discord_user_id, stats)
                if success:
                    sent_count += 1

        return sent_count
