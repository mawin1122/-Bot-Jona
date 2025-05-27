import nextcord
from nextcord.ext import commands
import json
import os
from datetime import datetime

ROLES_FILE = "./database/roles.json"
DATABASE_FILE = "./database/database.json"

def save_to_database(user_id: int, link: str, amount, trans_type="admin delrole", by_admin: str = None):
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
        transaction_entry["by"] = by_admin

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


class delet_role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name='remove-role', description="ลบบทบาทออกจากระบบ")
    @commands.has_permissions(administrator=True)
    async def delrole(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role
    ):
        """ลบบทบาทจาก roles.json"""

        try:
            with open(ROLES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        role_id_str = str(role.id)
        if role_id_str in data:
            # เก็บราคาบทบาทก่อนลบ (ถ้ามี)
            price = data[role_id_str].get("price", 0)

            del data[role_id_str]
            with open(ROLES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # บันทึกประวัติการลบบทบาท
            admin_identity = f"{interaction.user.name} ({interaction.user.id})"
            save_to_database(
                user_id=interaction.user.id,
                link=f"ลบบทบาท {role.name} ({role.id})",
                amount=price,
                trans_type="admin delrole",
                by_admin=admin_identity
            )

            embed = nextcord.Embed(
                title="🗑️ ลบบทบาทสำเร็จ",
                description=f"บทบาท `{role.name}` ถูกลบออกจากระบบแล้ว",
                color=nextcord.Color.red()
            )
            embed.set_thumbnail(url=role.guild.icon.url if role.guild.icon else None)
            embed.add_field(name="🆔 ID บทบาท", value=role.id, inline=False)
            embed.add_field(name="📅 วันที่ลบ", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            embed.set_footer(text=f"ลบโดย {interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ ไม่พบบทบาท `{role.name}` ในระบบ", ephemeral=True)


def setup(bot):
    bot.add_cog(delet_role(bot))
    print("✅ delrole loaded successfully.")
