# cogs/ping.py
import discord
from discord.ext import commands
import time

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', aliases=['p'])
    async def ping(self, ctx):
        """Kiểm tra độ trễ của bot"""
        
        # Tính thời gian phản hồi
        start_time = time.time()
        message = await ctx.send("🏓 Pong!")
        end_time = time.time()
        
        # Tính độ trễ
        api_latency = round(self.bot.latency * 1000, 2)  # WebSocket latency
        response_time = round((end_time - start_time) * 1000, 2)  # Response time
        
        # Tạo embed đẹp
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x00ff00 if api_latency < 100 else 0xffff00 if api_latency < 200 else 0xff0000
        )
        
        embed.add_field(
            name="📡 API Latency", 
            value=f"`{api_latency}ms`", 
            inline=True
        )
        
        embed.add_field(
            name="⚡ Response Time", 
            value=f"`{response_time}ms`", 
            inline=True
        )
        
        # Thêm emoji status dựa trên độ trễ
        if api_latency < 100:
            status = "🟢 Tuyệt vời!"
        elif api_latency < 200:
            status = "🟡 Bình thường"
        else:
            status = "🔴 Chậm"
            
        embed.add_field(
            name="📊 Status", 
            value=status, 
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        embed.timestamp = discord.utils.utcnow()
        
        # Edit message với embed
        await message.edit(content=None, embed=embed)

# Setup function để load cog
async def setup(bot):
    await bot.add_cog(Ping(bot))
