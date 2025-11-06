# Valorant Tracker Bot

A Python CLI tool to fetch and display Valorant player statistics from Tracker.gg API.

## Features

- Display overall season competitive stats
- Display last match performance
- Support for debug mode to see raw API responses

## Installation

This project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync
```

## Usage

### Season Stats (Default)

Display overall competitive stats for the current season:

```bash
uv run python main.py <username> <tag>
```

**Example:**
```bash
uv run python main.py AGreenFruit PEPE
```

**Output includes:**
- Current rank
- ACS (Average Combat Score)
- K/D ratio
- Win/loss record
- Damage per round
- Headshot percentage
- Total matches played

### Last Match Stats

Display stats from the most recent match:

```bash
uv run python main.py <username> <tag> --last
```

**Example:**
```bash
uv run python main.py AGreenFruit PEPE --last
```

**Output includes:**
- Map and mode
- Match result (Victory/Defeat)
- Agent played
- Final score
- Kills, deaths, assists
- K/D ratio
- Total damage
- Headshot percentage

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
uv run python main.py
```

You'll be prompted to enter the username and tag.

### Debug Mode

View the raw API response:

```bash
uv run python main.py <username> <tag> --debug
```

Can be combined with `--last`:

```bash
uv run python main.py <username> <tag> --last --debug
```

## Requirements

- Python 3.13+
- `requests` library (installed via `uv sync`)

## Notes

- The Tracker.gg public API doesn't require an API key
- Rate limits may apply for excessive requests
- Player profiles must be public to view stats
