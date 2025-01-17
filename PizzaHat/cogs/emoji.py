import asyncio

import discord
import yarl
from core.bot import PizzaHat
from core.cog import Cog
from discord.ext import commands
from discord.ext.commands import Context


# credits to R.Danny:
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/emoji.py
class EmojiURL:
    def __init__(self, *, animated: bool, url: str):
        self.url: str = url
        self.animated: bool = animated

    @classmethod
    async def convert(cls, ctx: Context, argument):
        try:
            partial = await commands.PartialEmojiConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                url = yarl.URL(argument)
                if url.scheme not in ('http', 'https'):
                    raise RuntimeError
                path = url.path.lower()
                if not path.endswith(('.png', '.jpeg', '.jpg', '.gif')):
                    raise RuntimeError
                return cls(animated=url.path.endswith('.gif'), url=argument)
            except Exception:
                raise commands.BadArgument('Not a valid or supported emoji URL.') from None
        else:
            return cls(animated=partial.animated, url=str(partial.url))

class Emojis(Cog, emoji="😀"):
    """Emoji management commands."""
    def __init__(self, bot: PizzaHat):
        self.bot: PizzaHat = bot

    @commands.group(name="emoji")
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def _emoji(self, ctx: Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @_emoji.command()
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_emojis=True)
    async def create(self, ctx: Context, emoji: EmojiURL, name):
        """
        Creates an emoji for the server under the given name.
        
        In order for this to work, the bot must have Manage Emojis permissions.

        To use this command, you must have Manage Emojis permission.
        """
        
        if ctx.guild is not None:
            emoji_count = sum(e.animated == emoji.animated for e in ctx.guild.emojis)

            if emoji_count >= ctx.guild.emoji_limit:
                return await ctx.send('There are no more emoji slots in this server.')

            async with self.bot.session.get(emoji.url) as resp:
                if resp.status >= 400:
                    return await ctx.send('Could not fetch the image.')

                if int(resp.headers['Content-Length']) >= (256 * 1024):
                    return await ctx.send('Image is too big.')

                data = await resp.read()
                coro = ctx.guild.create_custom_emoji(name=name, image=data, reason=f"Action done by {ctx.author}")

                try:
                    created = await asyncio.wait_for(coro, timeout=10.0)

                except asyncio.TimeoutError:
                    return await ctx.send('Sorry, the bot is rate limited or it took too long.')

                except discord.HTTPException as e:
                    return await ctx.send(f"Failed to create emoji: {e}")

                else:
                    return await ctx.send(f"Created {created}")    

    @_emoji.command()
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_emojis=True)
    async def delete(self, ctx: Context, emoji: discord.Emoji):
        """
        Deletes an emoji from the server.
        
        In order for this to work, the bot must have Manage Emojis permissions.

        To use this command, you must have Manage Emojis permission.
        """

        await emoji.delete(reason=f"Action done by {ctx.author}")
        await ctx.send(f"{self.bot.yes} Emoji successfully deleted.")


async def setup(bot):
    await bot.add_cog(Emojis(bot))
