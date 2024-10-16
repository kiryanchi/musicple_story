

    @commands.Cog.listener()
    async def on_ready(self):
        # 버튼 사용
        DiscordComponents(self.app)

        # '음악봇' 채널 가져오기
        channel = self.app.get_channel(self.MUSIC_CHANNEL)

        # 재생목록 및 플레이어 만들기
        player_embed = discord.Embed(title="현재 재생 중 아님", color=0xb18cfe)
        player_embed.set_image(url='https://s3.us-west-2.amazonaws.com/secure.notion-static.com/5b19c3df-c369-42fb-89b7-150cf832c800/996283.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20210730%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20210730T080909Z&X-Amz-Expires=86400&X-Amz-Signature=4dc106116bff4e5d7c1510def520dde106cb15bbfd69974f3cff0c6ae1cd3b6f&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22996283.jpg%22')
        player_embed.set_footer(text="채팅을 치면 자동으로 검색됩니다.")
        await channel.send(embed=player_embed, components = [
            [
                Button(style=ButtonStyle.green, label="Skip"),
                Button(style=ButtonStyle.grey, label="Shuffle"),
                Button(style=ButtonStyle.red, label="Stop")
            ]
        ])
        await channel.send("___***재생목록:***___")
        self.play_list = await channel.send("현재 재생목록 비어있음")

        # while True:
        #     interaction = await self.app.wait_for("button_click")

        #     if interaction.component.label == "Skip":
        #         await self.skip()
        #     elif interaction.component.label == "Shuffle":
        #         pass
        #     elif interaction.component.label == "Stop":
        #         pass
            

    # when message entered, search message in youtube
    async def search_music(self, message):
        NUM_OF_SEARCH = 10
        search_video = VideosSearch(message.content, limit=NUM_OF_SEARCH)
        search_result = {}

        for i in range(NUM_OF_SEARCH):
            info = {}
            info["title"] = search_video.result()["result"][i]["title"]
            info["link"] = search_video.result()["result"][i]["link"]
            info["duration"] = search_video.result()["result"][i]["duration"]
            search_result[i+1] = info

        # make search result to embed
        embed = discord.Embed(title="유튜브 검색결과", description="ㅤㅤㅤ", color=0xb18cfe)
        embed.set_author(name="노래 검색", icon_url="https://s3.us-west-2.amazonaws.com/secure.notion-static.com/1fd04c5e-a954-46dc-9ad3-2cd7d99d5612/pngwing.com.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20210730%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20210730T044245Z&X-Amz-Expires=86400&X-Amz-Signature=bc40771af81be3b77030a39f961fce7f9d4441a326b394c05a08c1e10cbe94e0&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22pngwing.com.png%22")
        embed.set_thumbnail(url="https://s3.us-west-2.amazonaws.com/secure.notion-static.com/1fd04c5e-a954-46dc-9ad3-2cd7d99d5612/pngwing.com.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20210730%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20210730T044245Z&X-Amz-Expires=86400&X-Amz-Signature=bc40771af81be3b77030a39f961fce7f9d4441a326b394c05a08c1e10cbe94e0&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22pngwing.com.png%22")

        for i in range(NUM_OF_SEARCH):
            embed.add_field(name=f"{i+1:2d}번\t({search_result[i+1]['duration']})", value=f"{search_result[i+1]['title']}", inline=False)

        # send search result embed to music channel
        msg = await message.channel.send(embed=embed, components = [
            [
                Button(label="1"),
                Button(label="2"),
                Button(label="3"),
                Button(label="4"),
                Button(label="5")
            ],
            [
                Button(label="6"),
                Button(label="7"),
                Button(label="8"),
                Button(label="9"),
                Button(label="10")
            ],
        ])

        # notice what user that sent message clicked
        def check(res):
            return message.author == res.user and res.channel == message.channel

        # if user select number in 10 sec, play music
        # but over 10 sec, send a message '10초내로 골라주세요.'
        # after finally, delete message
        try:
            res = await self.app.wait_for("button_click", check=check, timeout=10)
            select_num = int(res.component.label)
            await message.channel.send(f"{search_result[select_num]['title']} 선택됨", delete_after=5)
        except TimeoutError:
            await message.channel.send('10초내로 골라주세요.', delete_after=5)
        await msg.delete()
        await message.delete()

        with youtube_dl.YoutubeDL(self.YDL_OPTS) as ydl:
            try:
                info = ydl.extract_info(search_result[select_num]['link'], download=False)
            except:
                return None

        return {'link': info['formats'][0]['url'], 'title': info['title']}

    async def play_next(self):
        if len(self.play_list_queue) > 0:
            self.is_playing = True

            m_link = self.play_list_queue[0][0]['link']

            self.play_list_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_link, **self.FFMPEG_OPTIONS), after=lambda e: self.app.loop.create_task(self.play_next()))
        else:
            self.is_playing = False

    async def play_music(self):
        if len(self.play_list_queue) > 0:
            self.is_playing = True

            m_link = self.play_list_queue[0][0]['link']

            if self.vc == "" or not self.vc.is_connected() or self.vc is None:
                self.vc = await self.play_list_queue[0][1].connect()
            else:
                await self.vc.move_to(self.play_list_queue[0][1])

            print(self.play_list_queue)

            self.play_list_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_link, **self.FFMPEG_OPTIONS), after=lambda e: self.app.loop.create_task(self.play_next()))
        else:
            self.is_playing = False

    @commands.command()
    async def skip(self):
        if self.vc != "" and self.vc:
            self.vc.stop()
            await self.play_next()

    @commands.Cog.listener()
    async def on_message(self, message):
        # if bot, return
        if message.author == self.app.user:
            return
        # if not music channel, return and pass command
        if message.channel.id != self.MUSIC_CHANNEL:
            await self.app.process_commands(message)
            return

        # check author's voice channel. if None do not anything.
        if message.author.voice is None:
            await message.channel.send("음성 채널에 들어가서 사용해주세요", delete_after=5)
            await message.delete()
        else:
            voice_channel = message.author.voice.channel
            song = await self.search_music(message)
            if song:
                self.play_list_queue.append([song, voice_channel])
                if not self.is_playing:
                    await self.play_music()