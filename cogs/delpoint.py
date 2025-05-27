import nextcord
from nextcord.ext import commands
import json
import os
from datetime import datetime

DATABASE_FILE = "./database/database.json"

def save_to_database(user_id: int, link: str, amount, trans_type="admin add", by_admin: str = None):
    # amount รับได้ทั้ง str หรือ int/float แต่จะถูกแปลงเป็น float ภายใน

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
        "amount": float(amount),  # แปลงเป็น float
        "timestamp": timestamp
    }

    user_id_str = str(user_id)
    if by_admin:
        transaction_entry["by"] = by_admin  # เช่น "AdminName (ID)"
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
        
        
        
class RemovePoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @nextcord.slash_command(name='removepoint', description="ลบคะแนนจากผู้ใช้")
    @commands.has_permissions(administrator=True)
    async def removepoint(self, interaction: nextcord.Interaction, user: nextcord.User, points: int):
        """ลบคะแนนจากผู้ใช้ที่ระบุ"""
        # โหลดข้อมูลจากฐานข้อมูล
        if not os.path.exists(DATABASE_FILE):
            await interaction.response.send_message("❌ ยังไม่มีข้อมูลในระบบ", ephemeral=True)
            return

        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_id_str = str(user.id)

        if user_id_str not in data:
            await interaction.response.send_message(f"❌ ไม่พบข้อมูลของ {user.mention} ในระบบ", ephemeral=True)
            return

        current_amount = float(data[user_id_str].get("amount", 0))
        if points > current_amount:
            await interaction.response.send_message(f"❌ {user.mention} มีคะแนนไม่เพียงพอ (เหลือ {current_amount})", ephemeral=True)
            return

        # ลบคะแนน
        data[user_id_str]["amount"] = current_amount - points
        admin_identity = f"{interaction.user.name} ({interaction.user.id})"
        # บันทึกธุรกรรม
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction_entry = {
            "type": "admin remove",
            "link": f"ลบคะแนนจาก {user.id}",
            "amount": -points,
            "by_admin":admin_identity,
            "timestamp": timestamp
        }
        data[user_id_str]["transaction"].append(transaction_entry)

        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        await interaction.response.send_message(f"✅ ลบ {points} คะแนนจาก {user.mention}", ephemeral=True)

def setup(bot):
    bot.add_cog(RemovePoint(bot))
    print("AddPoint cog loaded successfully.")