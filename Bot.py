import re
import json
import asyncio
import yt_dlp
import aiohttp
import googleapiclient.discovery
import googleapiclient.errors
from discord.ext import commands


# 設定檔
with open("setting.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)
yt_client = googleapiclient.discovery.build(
    "youtube", "v3", developerKey=jdata["YoutubeAPI_Key"]
)

# 實例化物件
bot = commands.Bot(command_prefix="$")
ydl_opts = {
    "quiet": True,
    "hls_use_mpegts": True,
    "live_from_start": True,
    "outtmpl": "./video/%(title)s"
}

ydl = yt_dlp.YoutubeDL(ydl_opts)


# 正則表達式
re_syt = re.compile(r"https://youtu.be/([^ &#\n\?]+)", re.ASCII)
re_wyt = re.compile(r"https://www.youtube.com/watch(?:\?)v=([^ &#\n]+)", re.ASCII)
re_wlyt = re.compile(r"https://www.youtube.com/live/([^ &#\n\?]+)", re.ASCII)
re_ytshorts = re.compile(r"https://youtube.com/shorts/([^_&#\n\?]+)", re.ASCII)


async def get_yt_title(url):
    """
    取得 YouTube 影片標題
    """
    info = ydl.extract_info(url, download=False)
    return info.get("title", "") or "找不到，你確定這影片有標題？"


async def get_tags(title: str):
    """
    透過資料庫查詢是否有相關的字詞
    """
    session = aiohttp.ClientSession()
    if title:
        async with session.post(
            jdata["DataBase"], params={"method": "readTag", "query": title}
        ) as response:
            if response.status == 200:
                content = await response.text()
                content = content.translate({ord(c): None for c in '[]"'})
                words = content.split(",")
                unique_words = list(set(words))

                return " ".join(unique_words) or "找不到，你確定這你老婆的片？"
    session.close()

async def process_yt_link(msg, link):
    """
    處理 YouTube 連結
    """
    title = await get_yt_title(link)
    tags = await get_tags(title)
    await msg.channel.send(tags)


@bot.event
async def on_message(msg):
    """
    當有訊息時，檢查是否有 YouTube 連結，並且處理
    """
    context = str(msg.content)
    yt_link = (
        re_syt.search(context) or re_wyt.search(context) or re_ytshorts.search(context)
    )

    if yt_link:
        await process_yt_link(msg, yt_link.group())

    await bot.process_commands(msg)


async def record_live_stream(url):
    """
    錄製 YouTube 直播的異步函數
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))


@bot.command()
async def record(ctx, url: str):
    """
    錄製直播
    """
    asyncio.create_task(record_live_stream(url))
    await ctx.send("開始錄製直播!")


bot.run(jdata["Discord_Robot_Token"])
