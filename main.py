
from pyrogram import Client, filters
from pyrogram.types import Message
import os, json

# 🧩 مقادیر از محیط Render
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = int(os.getenv("SUDO_ID"))

# 🧠 ساخت یوزربات
app = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# 💬 پیام شروع
@app.on_message(filters.command(["start"]) & filters.user(SUDO_ID))
async def start(_, message: Message):
    await message.reply_text("✅ یوزربات با موفقیت فعاله و کار می‌کنه!")

# 💡 چک ساده برای اطمینان از کارکرد
@app.on_message(filters.text & filters.user(SUDO_ID))
async def echo(_, message: Message):
    text = message.text
    if text == "ping":
        await message.reply_text("🏓 pong!")
    elif text == "id":
        await message.reply_text(f"👤 آیدی عددی شما: <code>{message.from_user.id}</code>", parse_mode="html")

# 🚀 شروع اجرا
print("✅ Userbot is running...")
app.run()
