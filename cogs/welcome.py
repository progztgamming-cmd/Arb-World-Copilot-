import discord
from discord.ext import commands
from datetime import datetime, timezone

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        # بناء رسالة الترحيب
        embed = discord.Embed(
            title=f"🎉 أهلاً بك في Arb World | Welcome!",
            description=(
                f"مرحبًا {member.display_name}!\n"
                "نتمنى لك وقتًا ممتعًا في سيرفرنا 💙\n\n"
                "Welcome to Arb World! We're glad to have you here."
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=member.display_avatar.url)  # صورة كبيرة للبروفايل
        embed.add_field(
            name="📜 القوانين العامة | Server Rules",
            value=(
                "1. الاحترام المتبادل وعدم الإساءة.\n"
                "2. يمنع نشر أي بيانات شخصية.\n"
                "3. يمنع نشر الإعلانات أو روابط خارجية.\n"
                "4. يمنع السبام أو المينشن المفرط.\n"
                "5. يمنع نشر أي محتوى غير لائق.\n\n"
                "Enjoy your stay! ✨"
            ),
            inline=False
        )
        embed.set_footer(text="Arb World Copilot")

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            # إذا كانت الخاص مقفلة، لا مشكلة
            pass

async def setup(bot):
    await bot.add_cog(Welcome(bot))
