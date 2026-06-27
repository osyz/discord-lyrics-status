import asyncio
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
import syncedlyrics
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)


DISCORD_ENDPOINT = "https://discord.com/api/v9/users/@me/settings"
STATUS_FORMAT = "♪ {line}"
SCAN_DELAY = 0.30
IDLE_DELAY = 1.00
LYRIC_OFFSET = 0.50


@dataclass
class Track:
    title: str
    artist: str
    seconds: float
    playing: bool

    @property
    def query(self):
        return f"{self.title} {self.artist}".strip()


class Console:
    def __init__(self):
        self.message = "aguardando"

    def cursor(self, visible):
        sys.stdout.write("\033[?25h" if visible else "\033[?25l")
        sys.stdout.flush()

    def repaint(self, track=None, lyric=None):
        sys.stdout.write("\033[H\033[J")

        if not track:
            print("Now playing : procurando...")
        else:
            minutes, seconds = divmod(int(track.seconds), 60)
            print(f"Now playing : {track.title}")
            print(f"Artist      : {track.artist}")
            print(f"Position    : {minutes:02d}:{seconds:02d}")
            print(f"Line        : {(lyric or '...')[:70]}")

        print(f"Discord     : {self.message}")
        sys.stdout.flush()


class DiscordProfile:
    def __init__(self, token, console):
        self.token = token.strip().strip('"').strip("'")
        self.console = console

    def write(self, text=None):
        if not self.token:
            self.console.message = "token vazio"
            return

        body = {"custom_status": {"text": text}} if text else {"custom_status": None}
        headers = {
            "authorization": self.token,
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
        }

        try:
            response = requests.patch(
                DISCORD_ENDPOINT,
                headers=headers,
                json=body,
                timeout=5,
            )
        except requests.RequestException as error:
            self.console.message = f"erro de rede: {error}"
            return

        if response.ok:
            self.console.message = "status enviado"
        else:
            self.console.message = f"HTTP {response.status_code}: {response.text[:80]}"


class WindowsMedia:
    async def snapshot(self):
        try:
            manager = await MediaManager.request_async()
            session = manager.get_current_session()

            if not session:
                return None

            props = await session.try_get_media_properties_async()
            timeline = session.get_timeline_properties()
            drift = (
                datetime.now(timezone.utc) - timeline.last_updated_time
            ).total_seconds()

            return Track(
                title=props.title,
                artist=props.artist,
                seconds=timeline.position.total_seconds() + drift,
                playing=session.get_playback_info().playback_status == PlaybackStatus.PLAYING,
            )
        except Exception as error:
            return Track(
                title="Erro ao ler midia",
                artist=str(error),
                seconds=0,
                playing=False,
            )


class LyricBook:
    def __init__(self):
        self.cache = {}

    async def timeline_for(self, query):
        if query not in self.cache:
            raw = await asyncio.to_thread(syncedlyrics.search, query)
            self.cache[query] = self.parse(raw)
        return self.cache[query]

    def parse(self, raw):
        timeline = []
        pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")

        for row in (raw or "").splitlines():
            found = pattern.match(row)
            if not found:
                continue

            stamp = int(found[1]) * 60 + float(found[2])
            timeline.append((stamp, found[3].strip()))

        return sorted(timeline)

    def pick(self, timeline, seconds):
        selected = None

        for stamp, line in timeline:
            if stamp > seconds + LYRIC_OFFSET:
                break
            selected = line

        return self.clean(selected)

    def clean(self, line):
        if not line:
            return None

        line = line.replace("\r", "").strip()
        line = re.sub(r"([a-z])([A-Z])", r"\1 \2", line)

        symbol_ratio = len(re.sub(r"[a-zA-Z ]", "", line)) / max(len(line), 1)
        looks_joined = re.search(r"[a-z][A-Z][a-z]", line)

        if len(line) > 80 or symbol_ratio > 0.4 or looks_joined:
            return None
        if "/" in line and len(line) > 40:
            return None

        return line


class LyricsStatusApp:
    def __init__(self):
        self.console = Console()
        self.discord = DiscordProfile(read_token(), self.console)
        self.media = WindowsMedia()
        self.lyrics = LyricBook()
        self.song = None
        self.last_line = None
        self.timeline = []

    def send_later(self, text=None):
        asyncio.create_task(asyncio.to_thread(self.discord.write, text))

    async def change_song(self, track):
        self.song = track.query
        self.timeline = await self.lyrics.timeline_for(track.query)
        self.last_line = None
        self.send_later()

    async def run(self):
        os.system("cls" if os.name == "nt" else "clear")
        self.console.cursor(False)
        self.send_later()

        try:
            while True:
                track = await self.media.snapshot()

                if not track or not track.playing:
                    if self.last_line is not None:
                        self.last_line = None
                        self.send_later()
                    self.console.repaint()
                    await asyncio.sleep(IDLE_DELAY)
                    continue

                if track.query != self.song:
                    await self.change_song(track)

                line = self.lyrics.pick(self.timeline, track.seconds)
                if line != self.last_line:
                    self.last_line = line
                    self.send_later(STATUS_FORMAT.format(line=line) if line else None)

                self.console.repaint(track, line)
                await asyncio.sleep(SCAN_DELAY)
        finally:
            self.console.cursor(True)
            self.discord.write()


def read_token():
    token = os.getenv("DISCORD_TOKEN", "").strip()

    while not token:
        token = input("Cole seu token do Discord e aperte Enter: ").strip()
        if not token:
            print("Token vazio. Tente de novo.")

    return token


if __name__ == "__main__":
    try:
        asyncio.run(LyricsStatusApp().run())
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
