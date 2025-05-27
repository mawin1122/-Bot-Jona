import nextcord
from nextcord.ext import commands
import re
import tls_client
import json
import os
from datetime import datetime, timedelta
import asyncio
with open('config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

DATABASE_FILE = "./database/database.json"


ROLES_FILE = "./database/roles.json"

def save_to_database(user_id: int, link: str, amount: str, trans_type="topup"):
    # สร้างโฟลเดอร์ ./database หากยังไม่มี
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    # ถ้าไฟล์ database.json ยังไม่มี ให้สร้างเป็น dict ว่าง
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transaction_entry = {
        "type": trans_type,
        "link": link,
        "amount": amount,
        "timestamp": timestamp
    }

    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {
            "userid": user_id,
            "amount": amount,
            "total": amount,
            "transaction": [transaction_entry]
        }
    else:
        data[user_id_str]["transaction"].append(transaction_entry)

        current_amount = float(data[user_id_str]["amount"])
        current_total = float(data[user_id_str]["total"])
        added = float(amount)

        data[user_id_str]["amount"] = f"{current_amount + added:.2f}"
        data[user_id_str]["total"] = f"{current_total + added:.2f}"

    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_to_database_log(user_id: int, link: str, amount, trans_type="Buy", by_admin: str = None):
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

class topup_modal(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__("Top-up")
        self.bot = bot
        self.link = nextcord.ui.TextInput(
            label="Truemoney Gift Link",
            required=True,
            style=nextcord.TextInputStyle.short
        )
        self.add_item(self.link)

    async def callback(self, interaction: nextcord.Interaction):
        link = self.link.value.strip()
        match = re.match(r"https:\/\/gift\.truemoney\.com\/campaign\/\?v=([a-zA-Z0-9]+)", link)
        if not match:
            await interaction.response.send_message("❌ URL ไม่ถูกต้อง", ephemeral=True)
            return

        voucher_hash = match.group(1)

        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://gift.truemoney.com",
            "referer": "https://gift.truemoney.com/campaign/card",
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "accept-language": "th-TH,th;q=0.9,en;q=0.8",
        }

        payload = {
            "mobile": config['phone'],
            "voucher_hash": voucher_hash
        }

        response = session.post(
            f"https://gift.truemoney.com/campaign/vouchers/{voucher_hash}/redeem",
            headers=headers,
            json=payload
        )

        print("✅ Status:", response.status_code)
        print("🔄 Response:", response.text)

        if response.status_code == 200:
            redeemdata = response.json()
            if redeemdata["status"]["code"] == "SUCCESS":
                amount = float(redeemdata["data"]["my_ticket"]["amount_baht"])
                save_to_database(
                    user_id=interaction.user.id,
                    link=link,
                    amount=amount
                )
                print(f"✅ เติมเงินสำเร็จ จำนวน: {amount} บาท")

                await interaction.response.send_message(f"✅ เติมเงินสำเร็จ จำนวน: {amount} บาท", ephemeral=True)

                channel = self.bot.get_channel(int(config['log_channel_id']))  # แทนที่ด้วย ID ช่องที่ต้องการส่ง log
                if channel:
                    embed = nextcord.Embed(
                        title="💰 เติมเงิน TrueMoney Wallet",
                        description=f"🎉 **ผู้ใช้**: {interaction.user.mention}\n💵 **จำนวน**: {amount} บาท\n🔗\n```{link}```",
                        color=0x00ff41,
                        timestamp=datetime.now()
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    await channel.send(embed=embed)
            else:
                msg = redeemdata["status"].get("message", "เกิดข้อผิดพลาด")
                await interaction.response.send_message(f"❌ ล้มเหลว: {msg}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ ข้อผิดพลาด HTTP {response.status_code}", ephemeral=True)



class RoleSelect(nextcord.ui.Select):
    def __init__(self, bot, guild: nextcord.Guild):
        self.bot = bot
        self.guild = guild

        with open(ROLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        options = []
        for _, info in data.items():
            role_id = info.get("roleid")
            role = guild.get_role(int(role_id)) if role_id else None
            if role:
                label = info.get("label")
                if not label:
                    label = role.name
                description = info.get("description", "")
                emoji = info.get("emoji", None)
                options.append(
                    nextcord.SelectOption(
                        label=label,
                        value=str(role.id),
                        description=description,
                        emoji=emoji
                    )
                )


        # ✅ เพิ่มตัวเลือก "รีเซ็ต"
        options.append(
            nextcord.SelectOption(
                label="รีเซ็ตหน้าต่าง",
                value="reset",
                description="คลิกเพื่อรีเซ็ตเมนู",
                emoji="🔄"
            )
        )

        super().__init__(placeholder="เลือก Role ที่คุณต้องการ...", options=options, custom_id="role_select")
    async def callback(self, interaction: nextcord.Interaction):
        selected_value = self.values[0]

        if selected_value == "reset":
            # รีเซ็ต View ใหม่
            await interaction.response.edit_message(content=None, view=TopupView(self.bot, self.guild))
            return

        selected_role_id = int(selected_value)
        role = interaction.guild.get_role(selected_role_id)

        with open(ROLES_FILE, "r", encoding="utf-8") as f:
            roles_data = json.load(f)

        role_price = roles_data[selected_value]["price"]

        embed = nextcord.Embed(
            title="คุณเลือก Role",
            description=f"Role: {role.name}\nราคา: {role_price} บาท",
            color=0x00ff41,
            timestamp=datetime.now()
        )

        thumbnail_url = role.icon.url if role.icon else interaction.user.display_avatar.url

        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=f"ID: {role.id}")

        if role:
            await interaction.response.send_message(
                embed=embed,
                view=ConfirmView(self.bot, self.guild, selected_role_id),
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ ไม่พบ Role ที่เลือก", ephemeral=True)




class ConfirmView(nextcord.ui.View):
    def __init__(self, bot, guild, role_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild = guild
        self.role_id = role_id

    @nextcord.ui.button(label="ยืนยัน", style=nextcord.ButtonStyle.success)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        role = interaction.guild.get_role(self.role_id)

        # โหลดฐานข้อมูล
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            database = json.load(f)

        with open(ROLES_FILE, "r", encoding="utf-8") as f:
            roles_data = json.load(f)

        if user_id not in database:
            return await interaction.response.send_message("❌ ไม่พบข้อมูลของคุณในระบบ", ephemeral=True)

        if str(self.role_id) not in roles_data:
            return await interaction.response.send_message("❌ ไม่พบข้อมูล Role นี้ในระบบ", ephemeral=True)

        role_price = roles_data[str(self.role_id)]["price"]
        user_amount = database[user_id]["amount"]

        if user_amount < role_price:
            return await interaction.response.send_message(f"❌ ยอดเงินไม่เพียงพอ ({user_amount}/{role_price})", ephemeral=True)

        # หักเงินจากผู้ใช้
        database[user_id]["amount"] -= role_price

        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
            
        admin_identity = f"{interaction.user.name} ({interaction.user.id})"
        
        # เรียกฟังก์ชันบันทึกประวัติ โดยส่ง amount เป็นจำนวนเงินที่หัก (role_price)
        save_to_database_log(
            user_id=interaction.user.id,
            amount=role_price,      # เปลี่ยนจาก points เป็น role_price
            link=f"ได้ซื้อยศ {role.name} - {role.id}",               # ถ้ามีลิงก์เกี่ยวข้อง ใส่ได้
            by_admin=admin_identity
        )
            
        channel = self.bot.get_channel(int(config['log_buy']))  # ID ช่องแชนแนลสำหรับส่ง log
        if channel:
            embed_log = nextcord.Embed(
                title="💰 การซื้อบทบาทสำเร็จ",
                description=(
                    f"🎉 ผู้ใช้: {interaction.user.mention}\n"
                    f"🔖 บทบาทที่ได้รับ: **{role.name}**\n"
                    f"💵 ราคา: **{role_price}** บาท"
                ),
                color=0x00ff41,
                timestamp=datetime.now()
            )
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            await channel.send(embed=embed_log)
        
        # เพิ่มบทบาทให้ผู้ใช้
        await interaction.user.add_roles(role)

        # ตอบกลับด้วย embed แจ้งเตือนสำเร็จ
        embed = nextcord.Embed(
            title="✅ Role ได้รับการเพิ่มแล้ว",
            description=f"คุณได้รับ Role: **{role.name}**\nราคา: **{role_price}** บาท",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID: {role.id}")

        await interaction.response.edit_message(embed=embed, view=None)



            

        
    @nextcord.ui.button(label="ยกเลิก", style=nextcord.ButtonStyle.danger)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(content="❌ การซื้อ Role ถูกยกเลิก", view=None)
        self.stop()

        


class TopupView(nextcord.ui.View):
    def __init__(self, bot, guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(RoleSelect(bot, guild))



    @nextcord.ui.button(label="เติมเงิน", style=nextcord.ButtonStyle.green, custom_id="topup_button", row=1)
    async def topup_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(topup_modal(self.bot))
        
    @nextcord.ui.button(label="พร้อมเพ", style=nextcord.ButtonStyle.blurple, custom_id="prompay", row=1)
    async def prompay(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        total_seconds = 10 * 60  # 10 นาที = 600 วินาที
        end_time = datetime.utcnow() + timedelta(seconds=total_seconds)

        # ส่ง embed ครั้งแรก
        embed = nextcord.Embed(
            title="💰 เติมเงิน TrueMoney Wallet",
            description=f"🎯 **ระบบเติมเงินอัตโนมัติ 24 ชั่วโมง**\n\nกรุณาเติมเงินภายใน 10:00\n\n⏳ เหลือเวลา: 10:00",
            color=0x00ff41,
            timestamp=datetime.utcnow()
        )
        embed.set_image(url="https://www.checkraka.com/uploaded/img/content/130026/aungpao_truewallet_03.jpg")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(1)

        for remaining_seconds in range(total_seconds - 1, -1, -1):
            # แปลงวินาทีให้เป็น นาที:วินาที (MM:SS)
            minutes, seconds = divmod(remaining_seconds, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            if remaining_seconds > 0:
                description = (
                    "🎯 **ระบบเติมเงินอัตโนมัติ 24 ชั่วโมง**\n\n"
                    f"กรุณาเติมเงินภายใน {time_str} นาที\n\n"

                )
            else:
                description = "🎯 **ระบบเติมเงินอัตโนมัติ 24 ชั่วโมง**\n\nหมดเวลาการเติมเงินแล้ว"

            new_embed = nextcord.Embed(
                title="💰 เติมเงิน TrueMoney Wallet",
                description=description,
                color=0x00ff41,
                timestamp=datetime.utcnow()
            )
            new_embed.set_image(url="https://www.checkraka.com/uploaded/img/content/130026/aungpao_truewallet_03.jpg")

            try:
                await interaction.edit_original_message(embed=new_embed)
            except Exception as e:
                print("Error editing message:", e)

            await asyncio.sleep(1)
        
    @nextcord.ui.button(label="เช็คยอดเงิน", style=nextcord.ButtonStyle.blurple, custom_id="check_balance_button", row=1)
    async def check_balance_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id_str = str(interaction.user.id)

        if not os.path.exists(DATABASE_FILE):
            await interaction.response.send_message("❌ ไม่พบฐานข้อมูล", ephemeral=True)
            return

        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                await interaction.response.send_message("❌ ไม่สามารถอ่านฐานข้อมูลได้", ephemeral=True)
                return

        if user_id_str not in data:
            await interaction.response.send_message("🔍 ยังไม่มีข้อมูลยอดเงินของคุณ", ephemeral=True)
            return

        amount = data[user_id_str].get("amount", "0.00")
        total = data[user_id_str].get("total", "0.00")
        embed = nextcord.Embed(
            title="💰 ยอดเงินของคุณ",
            description=f"ยอดเงินปัจจุบัน: {amount} บาท\nยอดสะสมทั้งหมด: {total} บาท",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @nextcord.ui.button(label="ดูประวัติการเติมเงิน", style=nextcord.ButtonStyle.grey, custom_id="view_history_button", row=1)
    async def view_history_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id_str = str(interaction.user.id)

        if not os.path.exists(DATABASE_FILE):
            await interaction.response.send_message("❌ ไม่พบฐานข้อมูล", ephemeral=True)
            return

        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                await interaction.response.send_message("❌ ไม่สามารถอ่านฐานข้อมูลได้", ephemeral=True)
                return

        if user_id_str not in data:
            await interaction.response.send_message("🔍 ยังไม่มีประวัติการเติมเงินของคุณ", ephemeral=True)
            return

        transactions = data[user_id_str].get("transaction", [])
        if not transactions:
            await interaction.response.send_message("🔍 ไม่มีประวัติการเติมเงิน", ephemeral=True)
            return

        history = ""
        for t in transactions[-5:]:
            type_ = t["type"]
            amount = t["amount"]
            timestamp = t["timestamp"]
            history += f"• `{type_}` | `{amount}` | `{timestamp}`\n"

        embed = nextcord.Embed(
            title="🧾 ประวัติการเติมเงิน",
            description=history,
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
           
            
            
class topup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # เพิ่ม persistent view เมื่อ bot พร้อมใช้งาน
        guild = self.bot.get_guild(int(config["guild"]))
        if guild:
            self.bot.add_view(TopupView(self.bot, guild))



    @nextcord.slash_command(name='setup_topup', description="ตั้งค่าระบบเติมเงิน (Admin only)")
    @commands.has_permissions(administrator=True)
    async def setup_topup_command(self, interaction: nextcord.Interaction):
        """คำสั่งสำหรับ Admin ในการตั้งค่าระบบเติมเงิน"""
        await interaction.response.send_message("ตั่งค่าสำเร็จ", ephemeral=True)
        embed = nextcord.Embed(
            title="💰 เติมเงิน TrueMoney Wallet",
            description="🎯 **ระบบเติมเงินอัตโนมัติ 24 ชั่วโมง**\n",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.set_image(url="https://www.checkraka.com/uploaded/img/content/130026/aungpao_truewallet_03.jpg")

        await interaction.channel.send(embed=embed, view=TopupView(self.bot, interaction.guild))

def setup(bot):
    bot.add_cog(topup(bot))
    print("✅ Topup cog loaded successfully.")