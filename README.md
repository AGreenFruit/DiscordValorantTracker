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
DB_NAME=valorant
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# API Keys
HENRIK_API_KEY=your_henrik_api_key
DISCORD_BOT_TOKEN=your_discord_bot_token
```

4. **Set up the database**

Create a PostgreSQL database named `valorant`:

```sql
CREATE DATABASE valorant;
```

The required tables (`players` and `match_stats`) will be created automatically on first run.

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
3. Schedule the tracker job to run every `TRACKER_INTERVAL_MINUTES` (default: 1 minute)
4. Listen for Discord commands

### Discord Commands

#### Add a Player to Track

```
!tracker add <username>#<tag>
```

#### Remove a Player from Tracking

```
!tracker remove <username>#<tag>
```

#### List Your Tracked Players

```
!tracker list
```

#### Check Bot Status

```
!ping
```

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
User: !tracker add <username>#<tag>
Bot: Creates Player(username="<username>", tag="<tag>", discord_id=123, hash="abc123")
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
- Check database exists

## Configuration

### Changing Tracker Interval

Edit `TRACKER_INTERVAL_MINUTES` at the top of `src/main.py`:

```python
TRACKER_INTERVAL_MINUTES = 1  # Change this value
```

### Changing Region

Edit `src/app/jobs/tracker_job.py`:

```python
region = 'na'  # Change to: eu, ap, kr, etc.
```

## Running as a Service

To run the bot in the background on Linux, create a systemd service:

```bash
sudo nano /etc/systemd/system/valorant-tracker.service
```

```ini
[Unit]
Description=Valorant Tracker Discord Bot
After=network.target postgresql.service

[Service]
Type=simple
User=<your-username>
WorkingDirectory=<path-to-project>/DiscordValorantTracker
ExecStart=<path-to-uv>/uv run python src/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable valorant-tracker
sudo systemctl start valorant-tracker
```

Useful commands:

```bash
sudo systemctl status valorant-tracker   # Check status
sudo journalctl -u valorant-tracker -f   # View live logs
sudo systemctl restart valorant-tracker  # Restart
sudo systemctl stop valorant-tracker     # Stop
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [Henrik's Valorant API](https://docs.henrikdev.xyz/) for providing match data
- [discord.py](https://discordpy.readthedocs.io/) for Discord bot framework
- [APScheduler](https://apscheduler.readthedocs.io/) for job scheduling
