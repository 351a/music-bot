import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, options='-vn'), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    if content.startswith('play '):
        song_query = content[5:].strip()
        if not song_query:
            await message.channel.send("Please provide a song name to play.")
            return

        if not message.author.voice:
            await message.channel.send("You need to be in a voice channel to play music!")
            return

        voice_channel = message.author.voice.channel
        voice_client = message.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()

        if not voice_client:
            voice_client = await voice_channel.connect()

        async with message.channel.typing():
            search_url = f"ytsearch:{song_query}"
            player = await YTDLSource.from_url(search_url, loop=bot.loop)
            voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await message.channel.send(f'Now playing: {player.title}')

    elif content == 'pause':
        voice_client = message.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await message.channel.send("Paused the music.")
        else:
            await message.channel.send("No music is playing to pause.")

    elif content == 'resume':
        voice_client = message.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await message.channel.send("Resumed the music.")
        else:
            await message.channel.send("No music is paused to resume.")

    elif content == 'leave':
        voice_client = message.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            await message.channel.send("Disconnected from the voice channel.")
        else:
            await message.channel.send("I'm not in a voice channel.")

    await bot.process_commands(message)

bot.run('YOUR_BOT_TOKEN')
