import discord
from discord.ext import commands
import asyncio

VOICE_CHANNEL_ID = 1534179066775732286

class VoiceSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        await self.connect_to_home()

    async def connect_to_home(self):
        channel = self.bot.get_channel(VOICE_CHANNEL_ID)
        if channel is None:
            print("❌ Voice channel not found.")
            return
        if not isinstance(channel, discord.VoiceChannel):
            print("❌ Channel is not a voice channel.")
            return

        # التحقق مما إذا كان البوت متصل بالفعل
        if self.bot.user in channel.members:
            # تحديث حالة الصمم الذاتي
            voice_state = channel.guild.voice_client
            if voice_state and voice_state.channel == channel:
                await voice_state.guild.change_voice_state(channel=channel, self_deaf=True)
            return

        # فصل من أي قناة حالية
        if self.bot.voice_clients:
            for vc in self.bot.voice_clients:
                if vc.guild == channel.guild:
                    await vc.disconnect()

        try:
            await channel.connect(self_deaf=True)
        except Exception as e:
            print(f"❌ Failed to connect to voice: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member != self.bot.user:
            return
        # إذا خرج البوت من القناة المطلوبة (أو انتقل لغيرها) يعيد الانضمام
        if after.channel is None or after.channel.id != VOICE_CHANNEL_ID:
            # انتظر قليلاً قبل إعادة المحاولة
            await asyncio.sleep(3)
            await self.connect_to_home()

async def setup(bot):
    await bot.add_cog(VoiceSystem(bot))
