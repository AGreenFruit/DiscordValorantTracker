# Valorant Tracker Bot

A Discord bot that automatically tracks Valorant competitive matches and sends real-time notifications to players when new matches are detected.

## Features

- 🎮 **Automatic Match Tracking** - Monitors player matches every 5 minutes
- 📊 **Rich Match Statistics** - Detailed stats including K/D/A, ACS, ADR, headshot %, and more
- 💬 **Discord Notifications** - Sends beautiful embedded DMs when new matches are detected
- 🔄 **Duplicate Prevention** - Hash-based system prevents duplicate notifications
- 👥 **Multi-Player Support** - Track unlimited players across different Discord users
- ⚡ **Real-Time Updates** - Notifications sent immediately when matches are detected

## Architecture

```
src/
├── main.py                          # Entry point with scheduler
├── app/
│   ├── bot/
│   │   └── discord_bot.py          # Discord bot commands (!tracker add)
│   ├── services/
│   │   └── discord_notifier.py     # Notification service
│   ├── jobs/
│   │   └── tracker_job.py          # Match tracking job
│   ├── models/
│   │   ├── player.py               # Player Pydantic model
│   │   └── match.py                # Match stats Pydantic model
│   └── database/
│       └── tables.py               # Database abstractions
├── utils/
│   ├── hash.py                      # Hash utilities
│   └── http.py                      # HTTP utilities
└── interfaces/
    └── job.py                       # Job interface
```

## Installation

### Prerequisites

- Python 3.13+
- PostgreSQL database
- Discord bot token
- Henrik's Valorant API key

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd valorant-tracker-bot
```

2. **Install dependencies**
```bash
uv sync
uv pip install -e .
```

3. **Configure environment variables**

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_NAME=valorant_tracker
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# API Keys
HENRIK_API_KEY=your_henrik_api_key
DISCORD_BOT_TOKEN=your_discord_bot_token
```

4. **Set up the database**

Create the required tables:

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS valorant;

-- Players table
CREATE TABLE valorant.players (
    username VARCHAR(255) NOT NULL,
    tag VARCHAR(255) NOT NULL,
    discord_id BIGINT NOT NULL,
    hash VARCHAR(16) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match stats table
CREATE TABLE valorant.match_stats (
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
);
```

5. **Create a Discord bot**

- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application
- Go to "Bot" section and create a bot
- Enable "Message Content Intent" under Privileged Gateway Intents
- Copy the bot token and add it to your `.env` file
- Invite the bot to your server using OAuth2 URL Generator with:
  - Scopes: `bot`
  - Permissions: Send Messages, Read Message History

## Usage

### Starting the Bot

```bash
uv run python src/main.py
```

The bot will:
1. Connect to Discord
2. Run the tracker job immediately
3. Schedule the tracker job to run every 5 minutes
4. Listen for Discord commands

### Discord Commands

#### Add a Player to Track

```
!tracker add AGreenFruit#PEPE
```

This will:
- Parse the username and tag
- Store the player in the database with your Discord ID
- Generate a unique hash for the player
- Enable automatic match tracking

**Response:**
```
✅ Successfully added AGreenFruit#PEPE to tracking!
Discord User: @YourUsername
You will receive notifications when new matches are detected.
```

#### Check Bot Status

```
!ping
```

Returns the bot's latency.

### Match Notifications

When a new match is detected, you'll receive a Discord DM with:

**Embedded Message:**
- 🎮 **Title**: "New Match Detected!"
- **Color**: Green for Victory, Red for Defeat
- **Fields**:
  - Agent, Map, Result
  - Score (e.g., 13-11)
  - K/D/A (Kills/Deaths/Assists)
  - K/D Ratio
  - ACS (Average Combat Score)
  - ADR (Average Damage per Round)
  - Headshot %
  - Damage Δ (damage dealt - damage received)
  - Team Rank (your placement on your team, 1-5)
  - Match ID

## How It Works

### 1. Player Registration
```
User: !tracker add AGreenFruit#PEPE
Bot: Creates Player(username="AGreenFruit", tag="PEPE", discord_id=123, hash="abc123")
Database: Stores player with unique hash
```

### 2. Automatic Tracking (Every 5 Minutes)
```
1. Tracker job queries database for all players
2. Fetches latest competitive match for each player from Henrik's API
3. Generates match hash: hash(match_id:username#tag)
4. Attempts to insert match into database
5. If insert succeeds → new match detected
6. Sends Discord DM to player's discord_id
```

### 3. Duplicate Prevention
- **Player Hash**: `hash(username#tag:discord_id)` - Prevents duplicate player entries
- **Match Hash**: `hash(match_id:username#tag)` - Prevents duplicate match notifications

## API Reference

### Henrik's Valorant API

The bot uses Henrik's Valorant API v4:

```
GET https://api.henrikdev.xyz/valorant/v4/matches/{region}/pc/{username}/{tag}
```

**Parameters:**
- `region`: NA, EU, AP, etc.
- `mode`: competitive
- `size`: 1 (fetch only the latest match)

**Authentication:**
- Requires API key in `Authorization` header
- Get your key at: https://docs.henrikdev.xyz/

## Development

### Project Structure

- **Models**: Pydantic models for data validation
- **Services**: Business logic (notifications, etc.)
- **Jobs**: Background tasks (tracker job)
- **Database**: ORM-like table abstractions
- **Utils**: Shared utilities (hashing, HTTP)

### Adding New Features

1. **New Discord Command**: Add to `src/app/bot/discord_bot.py`
2. **New Job**: Create in `src/app/jobs/` and register in `src/main.py`
3. **New Model**: Add to `src/app/models/`
4. **New Database Table**: Add to `src/app/database/tables.py`

## Troubleshooting

### Bot doesn't respond to commands
- Verify "Message Content Intent" is enabled in Discord Developer Portal
- Check bot has permission to read/send messages in the channel

### Notifications not sending
- Ensure users have DMs enabled from server members
- Check database has players and match_stats tables
- Verify Henrik API key is valid

### Duplicate notifications
- Check that `hash` column has UNIQUE constraint in players table
- Verify `match_id` is PRIMARY KEY in match_stats table

### Database connection errors
- Verify database credentials in `.env`
- Ensure PostgreSQL is running
- Check database and schema exist

## Configuration

### Changing Tracker Interval

Edit `src/main.py`:

```python
scheduler.add_job(
    run_tracker_job,
    trigger=IntervalTrigger(minutes=5),  # Change this value
    ...
)
```

### Changing Region

Edit `src/app/jobs/tracker_job.py`:

```python
region = 'na'  # Change to: eu, ap, kr, etc.
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [Henrik's Valorant API](https://docs.henrikdev.xyz/) for providing match data
- [discord.py](https://discordpy.readthedocs.io/) for Discord bot framework
- [APScheduler](https://apscheduler.readthedocs.io/) for job scheduling
