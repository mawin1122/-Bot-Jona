import nextcord
from nextcord.ext import commands
from datetime import timedelta

anti = [1362163610289311947]

    
class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        
        
        

        # เช็คลิงก์ในข้อความ
        if 'http://' in message.content or 'https://' in message.content:
            if message.channel.id in anti:
                await message.delete()
                await message.author.timeout(timedelta(seconds=10), reason="ส่งลิงก์ต้องห้าม")
                await message.channel.send(f"{message.author.mention}, คุณไม่สามารถส่งลิงก์ในแชทนี้ได้ กรุณาอย่าส่งลิงก์.", delete_after=5)
                return
            else:

                return


        await self.bot.process_commands(message)

def setup(bot):
    bot.add_cog(AntiLink(bot))
    print("AntiLink cog loaded successfully.")