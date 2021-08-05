import discord
from discord.ext import commands


class Exp(commands.Cog):
    def __init__(self, app):
        self.app = app
    
    @commands.command(name='릴경')
    async def print_exp(self, ctx):
        await ctx.send('https://www.afreecatv.com/total_search.html?szSearchType=broad&szStype=di&szKeyword=%EB%A3%A8%EB%82%98%20%EB%A6%B4%EA%B2%BD&rs=1')


def setup(app):
    app.add_cog(Exp(app))