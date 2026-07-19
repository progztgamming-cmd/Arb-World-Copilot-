import discord
import requests
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Online"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = "MTUyODM0OTI4NDY4MzA4Nzg3Mg.GaTyxX.H96V-3N45re-ck_C1IcuGU-2Q609d8OM-1KgSI"
TEAM_ID = "d028d085fede4dbfda383cab901ce18105d6f1ec1e975d667fce7eb03dc4bbcd"
BOT_ID = "nYuFXohNxsLfgbet0XqG"

DOCSBOT_URL = f"https://api.docsbot.ai/v1/teams/{TEAM_ID}/bots/{BOT_ID}/ask"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Ready")
    await client.change_presence(activity=discord.Game(name="ARB WORLD Copilot"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or message.channel.name == "ask_arb_copilot":
        async with message.channel.typing():
            clean_text = message.content.replace(f'<@{client.user.id}>', '').strip()
            
            if not clean_text:
                await message.reply("Yes sir, I am listening. How can I help you?")
                return

            try:
                response = requests.post(DOCSBOT_URL, json={"question": clean_text})
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer found in documents.")
                    await message.reply(answer)
                else:
                    await message.reply("Error: Connection issue with DocsBot.")
            except Exception as e:
                await message.reply("Error: Failed to process request.")

keep_alive()
client.run(TOKEN)
              
