from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import discord
from discord.ext import commands, tasks

from config import (
    ASK_CHANNEL_ID,
    ASK_CLEANUP_INTERVAL_SECONDS,
    ASK_MESSAGE_LIFETIME_SECONDS,
    BAD_WORDS,
    CREW_CHAT_CHANNEL_ID,
    EXEMPT_ROLE_NAMES,
    GROQ_API_KEY,
    GROQ_FALLBACK_MODEL,
    GROQ_MODEL,
    LOGS_CHANNEL_ID,
)
from services.groq_service import GroqService
from services.knowledge_base import build_knowledge_context, detect_language


TEXTS = {
    "ar": {
        "warning": "تم حذف الرسالة لمخالفة قواعد السيرفر. كررها مرة ثانية ولن يكون الرد لطيفًا.",
        "invalid": "المعلومة دي مش كفاية. ابعتها بشكل أوضح.",
        "complaint_start": "تمام يا {user_mention}. ابعت اسم المشكو عليه.",
        "complaint_time": "ابعت زمن حدوث المشكلة.",
        "complaint_location": "ابعت أين حدثت المشكلة.",
        "complaint_content": "ابعت محتوى الشكوى.",
        "complaint_screenshot": "ابعت سكرين شوت أو اكتب تخطي.",
        "suggestion_start": "تمام يا {user_mention}. ابعت اسمك.",
        "suggestion_age": "ابعت عمرك.",
        "suggestion_content": "ابعت محتوى الاقتراح.",
        "bug_start": "تمام يا {user_mention}. ابعت اسمك.",
        "bug_location": "ابعت أين حدثت المشكلة.",
        "bug_repro": "ابعت كيف يمكننا تكرار المشكلة.",
        "bug_screenshot": "ابعت سكرين شوت للمشكلة.",
        "received": "تم استلام طلبك يا {user_mention}. الإدارة هتراجعه، ولو ما وصلكش حل افتح تذكرة.",
        "ai_prefix": "{user_mention} ",
    },
    "en": {
        "warning": "Your message was removed for breaking server rules. Repeat it and the response will be less polite.",
        "invalid": "That is not enough information. Please send a clearer answer.",
        "complaint_start": "Okay {user_mention}. Send the reported person's name.",
        "complaint_time": "Send the time the issue happened.",
        "complaint_location": "Send where it happened.",
        "complaint_content": "Send the complaint details.",
        "complaint_screenshot": "Send a screenshot or type skip.",
        "suggestion_start": "Okay {user_mention}. Send your name.",
        "suggestion_age": "Send your age.",
        "suggestion_content": "Send the suggestion details.",
        "bug_start": "Okay {user_mention}. Send your name.",
        "bug_location": "Send where the issue happened.",
        "bug_repro": "Send how to reproduce the issue.",
        "bug_screenshot": "Send a screenshot of the issue.",
        "received": "Your request was received, {user_mention}. Staff will review it, and if you do not get a solution, open a ticket.",
        "ai_prefix": "{user_mention} ",
    },
}


FORM_SCHEMAS = {
    "complaint": [
        ("target_name", True, "complaint_start"),
        ("time_occurred", True, "complaint_time"),
        ("location", True, "complaint_location"),
        ("content", True, "complaint_content"),
        ("screenshot", False, "complaint_screenshot"),
    ],
    "suggestion": [
        ("name", True, "suggestion_start"),
        ("age", True, "suggestion_age"),
        ("content", True, "suggestion_content"),
    ],
    "bug": [
        ("name", True, "bug_start"),
        ("location", True, "bug_location"),
        ("reproduction_steps", True, "bug_repro"),
        ("screenshot", True, "bug_screenshot"),
    ],
}


@dataclass
class IntakeSession:
    kind: str
    language: str
    step_index: int = 0
    answers: dict[str, str] = field(default_factory=dict)
    original_message: str = ""


class AskArbWorldCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.groq = GroqService(
            api_key=GROQ_API_KEY,
            models=[GROQ_MODEL, GROQ_FALLBACK_MODEL],
        )
        self.sessions: dict[int, IntakeSession] = {}
        self.user_languages: dict[int, str] = {}
        self.history: dict[int, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=10))

    async def cog_load(self) -> None:
        if not self.cleanup_loop.is_running():
            self.cleanup_loop.start()

    def cog_unload(self) -> None:
        if self.cleanup_loop.is_running():
            self.cleanup_loop.cancel()

    def _t(self, language: str, key: str, **kwargs: Any) -> str:
        lang = "ar" if language not in {"ar", "en"} else language
        template = TEXTS[lang][key]
        return template.format(**kwargs)

    def _is_exempt_member(self, member: discord.Member) -> bool:
        member_role_names = {role.name for role in member.roles}
        return any(role_name in member_role_names for role_name in EXEMPT_ROLE_NAMES)

    def _contains_bad_words(self, content: str) -> bool:
        lowered = (content or "").lower()
        return any(bad_word.lower() in lowered for bad_word in BAD_WORDS)

    def _is_plausible_text(self, text: str) -> bool:
        value = (text or "").strip()
        if len(value) < 2:
            return False
        if len(value) > 5000:
            return False
        if value.isdigit():
            return False
        if re.fullmatch(r"(.)\1{4,}", value):
            return False
        return True

    def _detect_intent(self, content: str) -> str:
        text = (content or "").lower()

        complaint_markers = ["شكوى", "شكو", "complaint", "report", "feedback", "abuse", "issue"]
        suggestion_markers = ["اقتراح", "suggestion", "idea", "improve", "improvement"]
        bug_markers = ["خطأ", "bug", "error", "glitch", "crash", "problem", "broken"]

        if any(marker in text for marker in complaint_markers):
            return "complaint"
        if any(marker in text for marker in suggestion_markers):
            return "suggestion"
        if any(marker in text for marker in bug_markers):
            return "bug"

        return "qa"

    def _schema(self, kind: str) -> list[tuple[str, bool, str]]:
        return FORM_SCHEMAS[kind]

    async def _send_log_embed(
        self,
        title: str,
        description: str,
        color: discord.Color,
        fields: list[tuple[str, str, bool]] | None = None,
    ) -> None:
        channel = self.bot.get_channel(LOGS_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(title=title, description=description, color=color)
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value or "None", inline=inline)
        await channel.send(embed=embed)

    async def _send_dm(self, member: discord.Member, title: str, description: str, color: discord.Color) -> None:
        embed = discord.Embed(title=title, description=description, color=color)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

    async def _acknowledge(self, message: discord.Message, language: str) -> None:
        await message.channel.send(
            f"{message.author.mention} {self._t(language, 'received', user_mention=message.author.mention)}",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )

    def _field_prompt(self, language: str, kind: str, step_index: int) -> str:
        field_name, required, prompt_key = self._schema(kind)[step_index]
        return self._t(language, prompt_key, user_mention="{user_mention}")

    async def _start_session(self, message: discord.Message, kind: str, language: str) -> None:
        session = IntakeSession(kind=kind, language=language, original_message=message.content or "")
        self.sessions[message.author.id] = session
        prompt = self._field_prompt(language, kind, 0)
        await message.channel.send(
            f"{message.author.mention} {prompt}",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )

    def _extract_field_value(self, message: discord.Message, field_name: str, required: bool) -> str | None:
        content = (message.content or "").strip()
        if field_name == "screenshot":
            if message.attachments:
                return message.attachments[0].url
            if content.lower() in {"skip", "no", "none", "n/a", "تخطي", "لا"}:
                return "" if not required else None
            if content:
                return content
            return None

        if not content:
            return None

        if not self._is_plausible_text(content):
            return None

        return content

    async def _finalize_session(self, message: discord.Message, session: IntakeSession) -> None:
        fields = []
        schema = self._schema(session.kind)

        for index, (field_name, required, prompt_key) in enumerate(schema):
            value = session.answers.get(field_name, "")
            pretty_name = field_name.replace("_", " ").title()
            fields.append((pretty_name, value or "None", False))

        description = f"Type: {session.kind}\nAuthor: {message.author} ({message.author.id})\nChannel: {message.channel.name}"
        await self._send_log_embed(
            title=f"Arb World {session.kind.title()} Intake",
            description=description,
            color=discord.Color.blue(),
            fields=fields,
        )

        await self._send_dm(
            message.author,
            title="Arb World Copilot",
            description="Your request has been received and forwarded to staff.",
            color=discord.Color.green(),
        )

        await self._acknowledge(message, session.language)
        self.sessions.pop(message.author.id, None)

    async def _answer_general_query(self, message: discord.Message, language: str) -> None:
        docs_context = build_knowledge_context(message.content)
        recent_history = list(self.history[message.author.id])[-8:]

        system_prompt = (
            "You are Arb World Copilot, a friendly support assistant for the Arb World server.\n"
            "Speak naturally and match the user's language.\n"
            "Always mention the user by name or mention at the start of the reply.\n"
            "Do not sound robotic.\n"
            "Use the official server docs if relevant.\n"
            "If the docs do not contain the answer, say that staff will verify it.\n"
            "Keep replies clear, short, and useful.\n"
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        if docs_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Official Arb World docs:\n\n{docs_context}",
                }
            )

        for item in recent_history:
            messages.append({"role": item["role"], "content": item["content"]})

        messages.append({"role": "user", "content": message.content})

        answer, _model = await self.groq.chat(messages)
        answer = answer.strip() or "I could not generate a useful reply."
        self.history[message.author.id].append({"role": "user", "content": message.content})
        self.history[message.author.id].append({"role": "assistant", "content": answer})

        await message.channel.send(
            f"{message.author.mention} {answer}",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )

    async def _handle_session_message(self, message: discord.Message, session: IntakeSession) -> None:
        schema = self._schema(session.kind)
        field_name, required, prompt_key = schema[session.step_index]
        value = self._extract_field_value(message, field_name, required)

        if value is None:
            await message.channel.send(
                f"{message.author.mention} {self._t(session.language, 'invalid')}",
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
            return

        session.answers[field_name] = value
        session.step_index += 1

        if session.step_index < len(schema):
            next_prompt = self._field_prompt(session.language, session.kind, session.step_index)
            await message.channel.send(
                f"{message.author.mention} {next_prompt}",
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
            return

        await self._finalize_session(message, session)

    async def _handle_bad_words(self, message: discord.Message) -> bool:
        if self._contains_bad_words(message.content):
            if isinstance(message.author, discord.Member) and self._is_exempt_member(message.author):
                return False

            try:
                await message.delete()
            except discord.HTTPException:
                pass

            await message.channel.send(
                f"{message.author.mention} {self._t(detect_language(message.content), 'warning')}",
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )

            await self._send_log_embed(
                title="Rule Violation",
                description="Bad word or direct insult removed in Ask channel.",
                color=discord.Color.red(),
                fields=[
                    ("Member", f"{message.author} ({message.author.id})", False),
                    ("Channel", f"{message.channel.name} ({message.channel.id})", False),
                    ("Content", message.content[:1000], False),
                ],
            )
            return True

        return False

    async def process_ask_message(self, message: discord.Message) -> None:
        if not message.guild:
            return

        language = self.user_languages.get(message.author.id) or detect_language(message.content or "")
        self.user_languages[message.author.id] = language

        if await self._handle_bad_words(message):
            return

        if message.author.id in self.sessions:
            await self._handle_session_message(message, self.sessions[message.author.id])
            return

        intent = self._detect_intent(message.content or "")
        if intent in {"complaint", "suggestion", "bug"}:
            await self._start_session(message, intent, language)
            return

        await self._answer_general_query(message, language)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.channel.id == ASK_CHANNEL_ID:
            await self.process_ask_message(message)

        await self.bot.process_commands(message)

    @tasks.loop(seconds=ASK_CLEANUP_INTERVAL_SECONDS)
    async def cleanup_loop(self) -> None:
        channel = self.bot.get_channel(ASK_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        cutoff = discord.utils.utcnow() - timedelta(seconds=ASK_MESSAGE_LIFETIME_SECONDS)
        active_session_users = set(self.sessions.keys())

        async for msg in channel.history(limit=100, oldest_first=False):
            if msg.pinned:
                continue
            if msg.author.bot and msg.created_at < cutoff.replace(tzinfo=None):
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
                continue

            if msg.author.bot:
                continue

            if msg.author.id in active_session_users:
                continue

            if msg.created_at < cutoff.replace(tzinfo=None):
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AskArbWorldCog(bot))
