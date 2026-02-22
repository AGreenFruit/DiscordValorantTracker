"""Main entry point for Valorant Tracker Bot with scheduled job"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.bot.discord_bot import bot
from app.services.discord_notifier import DiscordNotifier
from app.jobs.tracker_job import TrackerJob

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tracker interval in minutes
TRACKER_INTERVAL_MINUTES = 1

# Global scheduler
scheduler = AsyncIOScheduler()


async def run_tracker_job():
    """Run the tracker job and send notifications"""
    try:
        logger.info("Starting tracker job...")
        notifier = DiscordNotifier(bot)
        job = TrackerJob(notifier=notifier)
        result = await job.execute()
        logger.info(f"Tracker job completed: {result}")
    except Exception as e:
        logger.error(f"Error running tracker job: {e}", exc_info=True)


@bot.event
async def on_ready():
    """Event handler for when the bot is ready"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')

    # Start the scheduler
    if not scheduler.running:
        scheduler.add_job(
            run_tracker_job,
            trigger=IntervalTrigger(minutes=TRACKER_INTERVAL_MINUTES),
            id='tracker_job',
            name='Valorant Match Tracker',
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Scheduler started - tracker job will run every {TRACKER_INTERVAL_MINUTES} minute(s)")

        # Run the job immediately on startup
        await run_tracker_job()


async def main():
    """Main function to run the bot"""
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        raise ValueError("DISCORD_BOT_TOKEN is required to run the bot")

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
