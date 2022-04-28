import discord
from discord.ext import commands

from core.cog import Cog


def cog_help_embed(cog):
    title = cog.qualified_name or "No"
    em = discord.Embed(
        title=f'{title} Category',
        description=(
            f"{cog.full_description}\n\n"
            "`<>` required | `[]` optional"),
        color=discord.Color.blue()
    )

    for x in sorted(cog.get_commands(), key=lambda c: c.name):
        em.add_field(name=f"{x.name} {x.signature}", value=x.help, inline=False)

    em.set_footer(text='Use help [command] for more info')
    return em


class HelpDropdown(discord.ui.Select):
    def __init__(self, mapping: dict, ctx: commands.Context):
        self.cog_mapping = mapping
        self.ctx = ctx

        options = []
        for cog, _ in mapping.items():
            options.append(discord.SelectOption(
                label=cog.qualified_name,
                description=cog.description,
                emoji=cog.emoji
            ))

        super().__init__(
            placeholder="Choose a catagory...",
            min_values=1,
            max_values=1,
            options=sorted(options, key=lambda x: x.label)
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send(
                f"This help command was invoked by {self.ctx.author}\nThey can only use this.",
                ephemeral=True
            )

        cog_name = self.values[0]

        cog = None
        for c, _ in self.cog_mapping.items():
            if c and c.qualified_name == cog_name:
                cog = c
                break

        await interaction.message.edit(embed=cog_help_embed(cog))


class HelpView(discord.ui.View):
    def __init__(self, mapping: dict, ctx: commands.Context):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown(mapping, ctx))
        self.message = None

    async def on_timeout(self) -> None:
        self.children[0].disabled = True
        await self.message.edit(view=self)


class MyHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Help command for the bot",
                "cooldown": commands.CooldownMapping.from_cooldown(1, 3, commands.BucketType.user),
                "aliases": ['h']
            }
        )
    
    async def send(self, **kwargs):
        await self.get_destination().send(**kwargs)

    async def send_bot_help(self, mapping):
        ctx = self.context
        mapping = dict(filter(lambda x: x[0] and ctx.bot.cog_is_public(x[0]), mapping.items()))

        em = discord.Embed(
            title=f"{ctx.me.display_name} Help Menu",
            timestamp=ctx.message.created_at,
            color=discord.Color.blue()
        )
        em.set_thumbnail(url=ctx.me.avatar.url)

        em.description = ("Use `help [command | module]` for more info.\n")

        view = HelpView(mapping, self.context)
        view.message = await self.context.send(embed=em, view=view)

    async def send_command_help(self, command):
        if command.cog is None or not self.context.bot.cog_is_public(command.cog):
            return await self.send(content=f'No command called "{command}" found.')

        signature = self.get_command_signature(command)
        embed = discord.Embed(
            title=signature,
            description=command.help or "No help found...",
            color=discord.Color.blue()
        )

        if cog := command.cog:
            embed.add_field(name="Category", value=cog.qualified_name, inline=False)

        if command._buckets and (cooldown := command._buckets._cooldown):
            embed.add_field(
                name="Cooldown",
                value=f"{cooldown.rate} per {cooldown.per:.0f} seconds",
                inline=False,
            )

        await self.send(embed=embed)

    async def send_help_embed(self, title, description, commands):
        embed = discord.Embed(
            title=title,
            description=description or "No help found...",
            color=discord.Color.blue()
        )

        if filtered_commands := await self.filter_commands(commands):
            for command in filtered_commands:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.help or "No help found...",
                    inline=False)
        if not filtered_commands:
            await self.send("You don't have the required permissions for viewing this.")

        await self.send(embed=embed)

    async def send_group_help(self, group):
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog):
        if not self.context.bot.cog_is_public(cog):
            # pretend this hidden cog doesn't exist, send the same message the bot
            # would send if user uses p!help with an invalid cog name
            return await self.send(content=f'No command called "{cog.qualified_name}" found.')

        await self.send(embed=cog_help_embed(cog))

    async def send_error_message(self, error):
        channel = self.get_destination()
        await channel.send(error)


class Help(Cog, emoji="❓"):
    """Gives help on the bot."""

    def __init__(self, bot):
        self.bot = bot
        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command

def setup(bot):
    bot.add_cog(Help(bot))
