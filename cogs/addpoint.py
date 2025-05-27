import nextcord
from nextcord.ext import commands
import json
import os
from datetime import datetime

DATABASE_FILE = "./database/database.json"

def save_to_database(user_id: int, link: str, amount, trans_type="admin add", by_admin: str = None):
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transaction_entry = {
        "type": trans_type,
        "link": link,
        "amount": float(amount),
        "timestamp": timestamp,
    }

    if by_admin:
        transaction_entry["by"] = by_admin  # เช่น "AdminName (ID)"

    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {
            "userid": user_id,
            "amount": float(amount),
            "total": float(amount),
            "transaction": [transaction_entry]
        }
    else:
        data[user_id_str]["transaction"].append(transaction_entry)

        current_amount = float(data[user_id_str].get("amount", 0))
        current_total = float(data[user_id_str].get("total", 0))
        added = float(amount)

        data[user_id_str]["amount"] = current_amount + added
        data[user_id_str]["total"] = current_total + added

    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class AddPoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name='addpoint', description="เพิ่มคะแนนให้กับผู้ใช้")
    @commands.has_permissions(administrator=True)
    async def addpoint(self, interaction: nextcord.Interaction, user: nextcord.User, points: int):
        """เพิ่มคะแนนให้กับผู้ใช้ที่ระบุ"""
        admin_identity = f"{interaction.user.name} ({interaction.user.id})"
        save_to_database(
            user_id=user.id,
            amount=points,
            link=f"เพิ่มคะแนนให้ {user.id}",
            by_admin=admin_identity
        )

        await interaction.response.send_message(
            f"✅ เพิ่ม {points} คะแนนให้กับ {user.mention} โดย {interaction.user.mention}",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(AddPoint(bot))
    print("AddPoint cog loaded successfully.")
