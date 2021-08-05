import discord
from discord.ext import commands


class MonsterLife(commands.Cog):
    def __init__(self, app):
        self.app = app

    @commands.command(name='몬라')
    async def print_monster_life(self, ctx):
        await ctx.send("https://meso.kr/")
        await ctx.send("http://wachan.me/farm.php")

def setup(app):
    app.add_cog(MonsterLife(app))
