import discord
from discord.ext import commands
import datetime
from ruamel.yaml import YAML
from dotenv import load_dotenv
import os

load_env()
yaml = YAML()

with open("./config.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file)

INITIAL_EXTENSIONS = [
    'configuration.py',
    'cogs.dev',
    'cogs.events',
    'cogs.fun',
    'cogs.games',
    'cogs.help',
    'cogs.image',
    'cogs.mod',
    'cogs.music',
    'cogs.utility'
]

class PizzaHat(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("p!", "P!"),
            intents=discord.Intents.all(),
            case_insensitive=True,
            strip_after_prefix=True,
            activity=discord.Activity(type=discord.ActivityType.watching, name='dsc.gg/pizza-invite | discord.gg/WhNVDTF'),
            mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.yes = '<:yes:813819712953647206>'
        self.no = '<:no:829841023445631017>'
        self.color = discord.Color.blue()
        self.christmas = discord.Color.red()

        for extension in INITIAL_EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as e:
                print('Failed to load extension {}\n{}: {}'.format(
                    extension, type(e).__name__, e))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()
        print('Bot online')

bot = PizzaHat()
if __name__ == '__main__':
    bot.run(os.getenv("TOKEN"))
