import telebot
import os
from datetime import datetime
import pytz

# گرفتن توکن و آیدی از متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# ساعت ایران
iran_tz = pytz.timezone('Asia/Tehran')


# 🎬 شروع
@bot.message_handler(commands=['start', 'شروع'])
def start(message):
    bot.reply_to(message, "✅ ربات فعال شد و آماده محافظت از گروه است!\nبرای دیدن دستورات بنویسید: /دستورات")


# 📋 لیست دستورات
@bot.message_handler(commands=['help', 'دستورات'])
def help_command(message):
    text = (
        "🛡️ دستورات ربات محافظ:\n\n"
        "📌 /شروع - فعال‌سازی ربات\n"
        "📊 /آمار - نمایش تعداد اعضای گروه\n"
        "🕓 /ساعت - نمایش ساعت و تاریخ ایران\n"
        "🚫 /پاکسازی - حذف چند پیام آخر (فقط مدیر)\n"
        "ℹ️ /درباره - درباره‌ی ربات"
    )
    bot.reply_to(message, text)


# 🕓 نمایش ساعت
@bot.message_handler(commands=['ساعت'])
def show_time(message):
    now = datetime.now(iran_tz)
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y/%m/%d")
    bot.reply_to(message, f"🕓 ساعت فعلی ایران:\n⏰ {current_time}\n📅 تاریخ: {current_date}")


# 📊 آمار اعضای گروه
@bot.message_handler(commands=['آمار'])
def group_stats(message):
    if message.chat.type in ["group", "supergroup"]:
        count = bot.get_chat_members_count(message.chat.id)
        bot.reply_to(message, f"👥 تعداد اعضای گروه: {count}")
    else:
        bot.reply_to(message, "❗ این دستور فقط در گروه قابل استفاده است.")


# 🧹 پاکسازی پیام‌ها (فقط سودو)
@bot.message_handler(commands=['پاکسازی'])
def clear_messages(message):
    if message.from_user.id != SUDO_ID:
        bot.reply_to(message, "🚫 فقط مدیر اصلی می‌تواند از این دستور استفاده کند.")
        return
    try:
        for msg_id in range(message.message_id - 10, message.message_id):
            bot.delete_message(message.chat.id, msg_id)
        bot.send_message(message.chat.id, "🧹 چند پیام اخیر حذف شدند.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطا در پاکسازی: {e}")


# 🚫 حذف لینک‌ها (ضد تبلیغ)
@bot.message_handler(func=lambda msg: msg.text and ("http" in msg.text.lower() or "t.me/" in msg.text.lower()))
def block_links(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "🚫 ارسال لینک در این گروه ممنوع است!")
    except:
        pass


# ℹ️ درباره
@bot.message_handler(commands=['درباره'])
def about(message):
    bot.reply_to(message, "🤖 ربات محافظ فارسی نسخه‌ی Render\n👨‍💻 توسعه‌دهنده: محمد\n🛡️ وظیفه: محافظت از گروه و نمایش اطلاعات")


print("✅ Bot is running...")
bot.infinity_polling()
