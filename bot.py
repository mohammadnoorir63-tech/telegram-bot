import telebot
import json
import os
import re
import time
import requests

# ==============================
# تنظیمات اصلی
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID", 0))  # آیدی مدیر اصلی (سودو)

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
# فایل داده‌ها
# ==============================
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"groups": {}, "users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ==============================
# حذف Webhook (برای جلوگیری از خطای 409)
# ==============================
def delete_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Webhook removed successfully")
    except Exception as e:
        print("⚠️ Error deleting webhook:", e)

# ==============================
# افزودن کاربر جدید
# ==============================
def add_user(user_id):
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

# ==============================
# پیام خوش‌آمد /start
# ==============================
@bot.message_handler(commands=['start'])
def start_handler(message):
    add_user(message.chat.id)
    if message.chat.type == "private":
        bot.reply_to(message, "👋 سلام! من ربات محافظ گروه هستم.\nمرا به گروه اضافه کنید تا لینک و اسپم را حذف کنم.")
    else:
        bot.reply_to(message, "✅ ربات در گروه فعال شد و آماده محافظت است!")

# ==============================
# ضد لینک و اسپم
# ==============================
@bot.message_handler(func=lambda message: True)
def protect_group(message):
    try:
        # ضد لینک تلگرام
        if re.search(r"(t\.me/|telegram\.me/)", message.text or ""):
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🚫 ارسال لینک ممنوع است @{message.from_user.username or message.from_user.id}")
            return
        
        # ضد اسپم ساده
        if len(message.text or "") > 200:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "🚫 پیام بیش از حد طولانی حذف شد.")
            return
    except Exception as e:
        print("⚠️ Error in message handler:", e)

# ==============================
# دستور سودو /broadcast
# ==============================
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != SUDO_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "❗️متن پیام را بعد از دستور بنویسید.")
        return
    data = load_data()
    for user in data["users"]:
        try:
            bot.send_message(user, text)
        except:
            pass
    bot.reply_to(message, "✅ پیام برای همه کاربران ارسال شد.")

# ==============================
# راه‌اندازی ربات
# ==============================
if __name__ == "__main__":
    print("🧹 Removing webhook before polling...")
    delete_webhook()
    time.sleep(2)
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True)
