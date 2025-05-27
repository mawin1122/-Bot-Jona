import nextcord
from nextcord.ext import commands
import json
import os
from datetime import datetime

DATABASE_FILE = "./database/database.json"

class Checkpoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name='checkpoint', description="ตรวจสอบคะแนนของผู้ใช้")
    @commands.has_permissions(administrator=True)
    async def checkpoint(self, interaction: nextcord.Interaction, user: nextcord.User = None):
        if user is None:
            user = interaction.user

        if not os.path.exists(DATABASE_FILE):
            await interaction.response.send_message("ไม่มีข้อมูลคะแนนในระบบ", ephemeral=True)
            return

        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_id_str = str(user.id)
        if user_id_str not in data:
            await interaction.response.send_message(f"{user.mention} ยังไม่มีคะแนนในระบบ", ephemeral=True)
            return

        user_data = data[user_id_str]
        amount = user_data.get("amount", 0)
        total = user_data.get("total", 0)
        transactions = user_data.get("transaction", [])

        embed = nextcord.Embed(title=f"📊 คะแนนของ {user.name}", color=nextcord.Color.blue())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="🆔 ID ผู้ใช้", value=user.id, inline=False)
        embed.add_field(name="💰 คะแนนปัจจุบัน", value=str(amount), inline=True)
        embed.add_field(name="📈 คะแนนรวม", value=str(total), inline=True)

        if transactions:
            history = ""
            for t in transactions[-5:]:  # แสดงรายการล่าสุด 5 รายการ
                type_ = t["type"]
                amount_ = t["amount"]
                timestamp = t["timestamp"]
                history += f"• `{type_}` | `{amount_}` | `{timestamp}`\n"
            embed.add_field(name="🧾 รายการล่าสุด", value=history, inline=False)
        else:
            embed.add_field(name="🧾 รายการล่าสุด", value="ไม่มีรายการ", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Checkpoint(bot))
    print("✅ Checkpoint cog loaded successfully.")
