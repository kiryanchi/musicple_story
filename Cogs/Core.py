import discord
from discord.ext import commands


class Core(commands.Cog):
    def __init__(self, app):
        self.app = app

    @commands.command(name='출력')
    async def printit(self, ctx):
        await ctx.send(":) Python Bot에 의해 동작됨")


def setup(app):
    app.add_cog(Core(app))
