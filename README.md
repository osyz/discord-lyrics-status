# Discord Lyrics Status

Real-time synced lyrics for your Discord status.

Discord Lyrics Status is a simple Windows Python script that detects the song
you are listening to, finds synchronized lyrics, and updates your Discord custom
status line by line as the music plays.

## Features

- Shows live synced lyrics in your Discord custom status
- Detects the current song through Windows media controls
- Works with Spotify and other compatible media players
- Clears your status automatically when the song stops
- Includes a small terminal dashboard with the current track and lyric line

## Requirements

- Windows 10 or 11
- Python 3.8+
- Spotify or another player integrated with Windows media controls
- Discord user token

> Warning: automating a user token may violate Discord's terms of service.
> Use at your own risk.

## Install

Open CMD in this folder and run:

```cmd
pip install -r requirements.txt
```

## Run

Simple way:

```cmd
python lyrics.py
```

If Windows uses the `py` launcher:

```cmd
py lyrics.py
```

When it starts, the script will ask for your Discord token if the
`DISCORD_TOKEN` environment variable is not configured.

## Optional: use an environment variable

In CMD:

```cmd
set DISCORD_TOKEN=YOUR_TOKEN_HERE
python lyrics.py
```

In PowerShell:

```powershell
$env:DISCORD_TOKEN="YOUR_TOKEN_HERE"
python lyrics.py
```

## Create an executable

Install PyInstaller:

```cmd
pip install pyinstaller
```

Build the executable:

```cmd
pyinstaller --onefile --name DiscordLyricsStatus lyrics.py
```

The final file will appear in:

```text
dist\DiscordLyricsStatus.exe
```

## License

This project is a modified version of software originally created by ashuni.

The original code is licensed under the MIT License. See `LICENSE` for the full
license text and `NOTICE.md` for authorship and modification notices.
