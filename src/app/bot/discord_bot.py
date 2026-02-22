"""Discord bot for Valorant tracker commands"""
import discord
from discord.ext import commands
import psycopg2
import os
import logging
from dotenv import load_dotenv

from app.models.player import Player
from app.database.tables import PlayersTable

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


class DatabaseConnection:
    """Context manager for database connections"""
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "valorant"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


@bot.command(name='tracker')
async def tracker(ctx, action: str = None, player_identifier: str = None):
    """
    Tracker command to manage player tracking.

    Usage:
        !tracker add <username>#<tag>
        !tracker remove <username>#<tag>
    """
    if action is None:
        await ctx.send(
            "**Valorant Tracker Bot**\n"
            "Usage:\n"
            "`!tracker add <username>#<tag>` - Start tracking a player\n"
            "`!tracker remove <username>#<tag>` - Stop tracking a player\n"
            "`!tracker list` - Show all players you're tracking"
        )
        return

    if action.lower() == 'add':
        if player_identifier is None:
            await ctx.send("❌ Please provide a player name in the format: `username#tag`")
            return

        # Parse the player identifier
        if '#' not in player_identifier:
            await ctx.send("❌ Invalid format. Please use: `username#tag` (e.g., `Player#Tag`)")
            return

        try:
            username, tag = player_identifier.split('#', 1)
            username = username.strip()
            tag = tag.strip()

            if not username or not tag:
                await ctx.send("❌ Both username and tag are required.")
                return

            # Get the Discord user ID
            discord_id = ctx.author.id

            # Create Player model
            player = Player(
                username=username,
                tag=tag,
                discord_id=discord_id
            )

            # Insert into database
            with DatabaseConnection() as (conn, cursor):
                players_table = PlayersTable(conn, cursor)
                success = players_table.insert(player)

                if success:
                    await ctx.send(
                        f"✅ Successfully added **{username}#{tag}** to tracking!\n"
                        f"Discord User: <@{discord_id}>\n"
                        f"You will receive notifications when new matches are detected."
                    )
                    logger.info(f"Added player {username}#{tag} for Discord user {discord_id}")
                else:
                    await ctx.send(
                        f"ℹ️ **{username}#{tag}** is already being tracked.\n"
                        f"You will continue to receive match notifications."
                    )

        except ValueError:
            await ctx.send("❌ Invalid format. Please use: `username#tag` (e.g., `Player#Tag`)")
        except Exception as e:
            logger.error(f"Error adding player: {e}")
            await ctx.send("❌ An error occurred while adding the player. Please try again later.")

    elif action.lower() == 'list':
        try:
            discord_id = ctx.author.id

            with DatabaseConnection() as (conn, cursor):
                cursor.execute(
                    "SELECT username, tag FROM players WHERE discord_id = %s ORDER BY created_at",
                    (discord_id,)
                )
                players = cursor.fetchall()

                if players:
                    player_list = "\n".join(
                        f"• **{username}#{tag}**" for username, tag in players
                    )
                    await ctx.send(
                        f"**Tracked Players ({len(players)}):**\n{player_list}"
                    )
                else:
                    await ctx.send(
                        "You're not tracking any players yet.\n"
                        "Use `!tracker add <username>#<tag>` to start tracking."
                    )

        except Exception as e:
            logger.error(f"Error listing players: {e}")
            await ctx.send("❌ An error occurred while fetching your tracked players.")

    elif action.lower() == 'remove':
        if player_identifier is None:
            await ctx.send("❌ Please provide a player name in the format: `username#tag`")
            return

        if '#' not in player_identifier:
            await ctx.send("❌ Invalid format. Please use: `username#tag` (e.g., `Player#Tag`)")
            return

        try:
            username, tag = player_identifier.split('#', 1)
            username = username.strip()
            tag = tag.strip()

            if not username or not tag:
                await ctx.send("❌ Both username and tag are required.")
                return

            discord_id = ctx.author.id

            with DatabaseConnection() as (conn, cursor):
                players_table = PlayersTable(conn, cursor)
                success = players_table.delete(username=username, tag=tag, discord_id=discord_id)

                if success:
                    await ctx.send(
                        f"✅ Successfully removed **{username}#{tag}** from tracking."
                    )
                    logger.info(f"Removed player {username}#{tag} for Discord user {discord_id}")
                else:
                    await ctx.send(
                        f"ℹ️ **{username}#{tag}** is not currently being tracked."
                    )

        except ValueError:
            await ctx.send("❌ Invalid format. Please use: `username#tag` (e.g., `Player#Tag`)")
        except Exception as e:
            logger.error(f"Error removing player: {e}")
            await ctx.send("❌ An error occurred while removing the player. Please try again later.")

    else:
        await ctx.send(
            f"❌ Unknown action: `{action}`\n"
            f"Available actions: `add`, `remove`, `list`"
        )


@bot.command(name='ping')
async def ping(ctx):
    """Simple ping command to test bot responsiveness"""
    await ctx.send(f'🏓 Pong! Latency: {round(bot.latency * 1000)}ms')


def run_bot():
    """Run the Discord bot"""
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        raise ValueError("DISCORD_BOT_TOKEN is required to run the bot")

    bot.run(token)


if __name__ == "__main__":
    run_bot()
