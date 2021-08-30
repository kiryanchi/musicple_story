import discord
from asyncio.exceptions import TimeoutError
from discord.ext import commands
from discord_components import DiscordComponents, Button, Select, SelectOption, ButtonStyle, InteractionType
from youtubesearchpython import VideosSearch
import youtube_dl
import random

class Music(commands.Cog):
    def __init__(self, app):
        DiscordComponents(app)
        self.app:commands.Bot = app

        # Constant    
        self.MUSIC_CHANNEL = 871350224499658833
        self.YDL_OPTS = {"format": "bestaudio", "quiet": False}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.NUM_OF_SEARCH = 9
        self.NUM_OF_SONG_QUEUE = 30
        self.PLAYER_EMBED_MSG_ID = 873180322299252766
        self.BUTTON_MSG_ID = 873180323490439199
        self.BUTTON_COMPONENTS = [
            [
                Button(style=ButtonStyle.green, label="Skip"),
                Button(style=ButtonStyle.grey, label="Shuffle"),
                Button(style=ButtonStyle.red, label="Pause"),
            ]
        ]

        # Variable
        self.song_queue = []
        self.is_playing = False
        self.vc = ""
        self.player_embed_msg = ""
        self.button_embed_msg = ""
    
    @commands.Cog.listener()
    async def on_ready(self):
        DiscordComponents(self.app)
        channel = self.app.get_channel(self.MUSIC_CHANNEL)
        self.player_embed_msg = await channel.fetch_message(self.PLAYER_EMBED_MSG_ID)
        self.button_embed_msg = await channel.fetch_message(self.BUTTON_MSG_ID)

        embed = self.make_song_embed()
        await self.player_embed_msg.edit("현재 재생목록 비어있음", embed=embed)
        # await self.button_embed_msg.edit(" ឵ ឵឵ ឵ ឵឵ ឵ ឵឵ ឵ ឵", components=self.BUTTON_COMPONENTS)
        # button embed 
        await self.button_reaction()

    async def button_reaction(self):
        await self.button_embed_msg.edit(" ឵ ឵឵ ឵ ឵឵ ឵ ឵឵ ឵ ឵", components=self.BUTTON_COMPONENTS)
        while True:
            res = await self.app.wait_for("button_click")
            if res.component.label == "Skip":
                await self.skip()
            elif res.component.label == "Shuffle":
                await self.shuffle()
            elif res.component.label == "Pause":
                self.pause()

    def make_song_embed(self, title=None, thumbnail=None):
        if thumbnail is not None:
            embed = discord.Embed(title="현재 재생 중인 곡", description=title, color=0xb18cfe)
            embed.set_image(url=thumbnail)
            embed.set_footer(text="채팅을 치면 자동으로 검색합니다.")
            self.is_playing = True
        else:
            embed = discord.Embed(title="현재 재생 중 아님", color=0xb18cfe)
            embed.set_image(url="")
            embed.set_footer(text="채팅을 치면 자동으로 검색합니다.")
            self.is_playing = False
        return embed

    async def skip(self):
        self.vc.stop()
        await self.check_queue()

    async def shuffle(self):
        random.shuffle(self.song_queue)
        await self.refresh_song_queue()

    def pause(self):
        if self.vc.is_paused():
            self.vc.resume()
        elif not self.vc.is_paused():
            self.vc.pause()

    async def search_song(self, amount, song, get_url=False):
        info = await self.app.loop.run_in_executor(None, lambda: VideosSearch(song, limit=self.NUM_OF_SEARCH))

        return info.result()

    async def select_song(self, title, info, message):
        embed = discord.Embed(title=f"{title} 검색 결과", description="ㅤㅤㅤ", color=0xb18cfe)
        embed.set_author(name="ㅤ", icon_url="")
        embed.set_thumbnail(url="")

        for i in range(self.NUM_OF_SEARCH):
            embed.add_field(name=f"{i+1:2d}번\t({info['result'][i]['duration']}) {info['result'][i]['channel']['name']}", value=f"제목: {info['result'][i]['title']}", inline=False)
        
        components = []
        for i in range(self.NUM_OF_SEARCH//5 + 1):
            component = []
            for j in range(5):
                if i*5 + j == self.NUM_OF_SEARCH:
                    break
                component.append(Button(label=i*5 + j + 1))
            components.append(component)
        
        components.append(Button(style=ButtonStyle.red, label="Cancel"))

        msg = await message.reply(embed=embed, components=components)


        def check(res):
            # TODO: 2개를 검색했을 때, 버튼이 2개 다 같은 번호를 선택하는 현상을 고쳐야함
            return message.author == res.user and res.channel == message.channel

        try:
            res = await self.app.wait_for("button_click", check=check, timeout=15)
            select = res.component.label
            if select == 'Cancel':
                # TODO: Cancel
                raise TimeoutError
            else:
                select = int(select)
        except TimeoutError:
            await msg.delete()
            await message.delete()
            await message.channel.send('노래 선택이 취소되었습니다.', delete_after=5)
            return None
        await msg.delete()
        await message.delete()

        return info['result'][select-1]

    async def check_queue(self):
        if len(self.song_queue) == 0:
            embed = self.make_song_embed()
            await self.player_embed_msg.edit(embed=embed)
            await self.vc.disconnect()
            # await self.app.voice_clients[0].disconnect()
        else:
            self.vc.stop()
            await self.play_song(self.song_queue[0])
            self.song_queue.pop(0)
            await self.refresh_song_queue()

    async def play_song(self, song_info):
        m_link = song_info[0]['link']

        with youtube_dl.YoutubeDL(self.YDL_OPTS) as ydl:
            info = ydl.extract_info(m_link, download=False)
            url = info['formats'][0]['url']

        if self.vc == "" or not self.vc.is_connected() or self.vc is None:
            self.vc = await song_info[1].connect()
        else:
            await self.vc.move_to(song_info[1])
        
        embed = self.make_song_embed(song_info[0]['title'], song_info[0]['thumbnails'][0]['url'])

        await self.player_embed_msg.edit(embed=embed)

        self.vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS)), after=lambda error: self.app.loop.create_task(self.check_queue()))
        self.vc.source.volume = 0.5

    async def refresh_song_queue(self):
        if len(self.song_queue) == 0:
            await self.player_embed_msg.edit("현재 재생목록 비어있음")
        elif len(self.song_queue) > 0:
            text = ""
            for idx in range(len(self.song_queue)):
                title = self.song_queue[idx][0]['title']
                text += f"[{idx+1}] {title}\n"
            # for info in self.song_queue:
            #     title = info[0]['title']
            #     text += f"{title}\n"
            await self.player_embed_msg.edit(text)

    @commands.command()
    async def init(self, ctx):
        await ctx.send("___***재생목록:***___")
        await ctx.send('재생목록이 될 메시지')
        await ctx.send(' ឵ ឵឵ ឵ ឵឵ ឵ ឵឵ ឵ ឵')

    @commands.Cog.listener()
    async def on_message(self, message):
        # if not music channel, return and pass command
        if message.channel.id != self.MUSIC_CHANNEL:
            # await self.app.process_commands(message)
            return
        # if bot, return
        if message.author == self.app.user:
            return

        # 검색자가 채널에 없는 경우
        if message.author.voice is None:
            # TODO: 지금은 그냥 노래 추가를 안 하지만 음악 재생중일 경우 그냥 queue에 추가하는 방향으로 추가
            await message.channel.send("음성 채널에 들어가서 사용해주세요", delete_after=5)
            return await message.delete()
            
        info = await self.search_song(self.NUM_OF_SEARCH, message.content)
        song = await self.select_song(message.content, info, message)

        voice_channel = message.author.voice.channel

        # 현재 문제상황
        # bot이 접속해있는지 확인하지 않고 그냥 바로 queue에 때려넣음
        # 그래서 노래가 끝나면 아예 연결을 끊도록 임시조치해둠.
        # 이게 문제 고치자.
        if song:
            if self.vc == "" or not self.vc.is_connected() or self.vc is None:
                self.vc = await voice_channel.connect()
            else:
                await self.vc.move_to(voice_channel)

            if self.vc.source is not None:
                if len(self.song_queue) < self.NUM_OF_SONG_QUEUE:
                    self.song_queue.append([song, voice_channel])
                    await self.refresh_song_queue()
                    return await message.channel.send(f"{song['title']} 이(가) 선택됨.", delete_after=5)
                else:
                    return await message.channel.send(f"재생목록 가득 참. 이 곡이 끝나면 추가해주세요.", delte_after=10)

            await self.play_song([song, voice_channel])

def setup(app):
    app.add_cog(Music(app))
