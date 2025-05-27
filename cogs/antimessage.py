import nextcord
from nextcord.ext import commands



class AntiMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        has_image = False
    # เช็ค attachment
        if message.attachments:
            # ถ้า attachment ตัวไหนเป็นไฟล์รูป (เช็คจากนามสกุล)
            for attachment in message.attachments:
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    has_image = True
                    break

        # หรือเช็ค embed ที่เป็นรูปภาพ (optional)
        if not has_image and message.embeds:
            for embed in message.embeds:
                if embed.image or embed.thumbnail:
                    has_image = True
                    break

        if has_image:
            # ข้อความมีรูปภาพ ไม่ต้องลบ
            await self.bot.process_commands(message)
            return
        # Check for specific words in the message
        if message.content in message.content.lower():
            
            if message.channel.id in [1362163610289311947]:
                
                await message.delete()
                return
            else:
                

                return

        await self.bot.process_commands(message)
        
def setup(bot):
    bot.add_cog(AntiMessage(bot))
    print("AntiMessage cog loaded successfully.")