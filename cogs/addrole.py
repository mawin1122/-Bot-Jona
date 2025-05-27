import nextcord
from nextcord.ext import commands
import json
import os
from datetime import datetime

DATABASE_FILE = "./database/database.json"
ROLES_FILE = "./database/roles.json"

def save_to_database(user_id: int, link: str, amount, trans_type="admin addrole", by_admin: str = None):
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

class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name='addrole', description="เพิ่มบทบาทให้กับผู้ใช้")
    @commands.has_permissions(administrator=True)
    async def addrole(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role,
        label: str,
        description: str,
        price: int,
        emoji: str
    ):
        """เพิ่มบทบาทใหม่ลงใน roles.json"""

        # โหลดข้อมูลเดิม
        try:
            with open(ROLES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        role_id_str = str(role.id)
        # เพิ่มหรือแก้ไขข้อมูล role
        data[role_id_str] = {
            "roleid": role.id,
            "label": label,
            "description": description,
            "price": price,
            "emoji": emoji
        }

        # บันทึกไฟล์ roles.json
        with open(ROLES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        admin_identity = f"{interaction.user.name} ({interaction.user.id})"
        
        # กำหนด link เป็น "-" หรือ URL ใด ๆ ที่ต้องการ
        link_placeholder = f"{role.id} - {role.name} price: {price} บาท" 

        # เรียกใช้ save_to_database โดยส่งข้อมูลครบ
        save_to_database(
            user_id=interaction.user.id,
            link=link_placeholder,
            amount=price,
            trans_type="admin addrole",
            by_admin=admin_identity
        )
        embed = nextcord.Embed(
            title="✅ บทบาทถูกเพิ่มเรียบร้อยแล้ว",
            description=f"บทบาท: {role.name}\nราคา: {price} บาท\nLabel: {label}\nDescription: {description}",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)



def setup(bot):
    bot.add_cog(RoleCog(bot))

        
