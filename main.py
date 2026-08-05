import discord
from discord.ext import commands
import os
import asyncio

# جلب التوكن والمفتاح من config.py أو من متغيرات البيئة
try:
    from config import DISCORD_TOKEN, GROQ_API_KEY
except ImportError:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# تعريف البوت مع كل الصلاحيات
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# قائمة الكوجات التي سنقوم بتحميلها
cogs_list = [
    'cogs.ask_arb_world',
    'cogs.moderation',
    'cogs.leveling',
    'cogs.welcome',
    'cogs.voice'
]

@bot.event
async def on_ready():
    print(f'✅ تم تشغيل البوت {bot.user} بنجاح')
    await bot.change_presence(activity=discord.Game(name="Arb World Copilot"))

async def load_cogs():
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f'🔹 Loaded {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
