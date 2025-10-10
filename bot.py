# -*- coding: utf-8 -*-
# Persian Lux Panel V18 – تماماً فارسی و سازگار با Render

import os
import json
import time
import telebot
from telebot import types
import jdatetime
import re

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
DATA_FILE = "data.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================= 💾 سیستم داده‌ها =================
def base_data():
    return {
        "locks": {},
        "welcome": {},
        "banned": {},
        "admins": {},
        "sudos": [],
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    if gid not in data["locks"]:
        data["locks"][gid] = {"link": False, "group": False}
    if gid not in data["welcome"]:
        data["welcome"][gid] = {"enabled": True}
    save_data(data)

# ================= 🕒 ابزارها =================
def now_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def now_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def cmd(m):
    return (m.text or "").strip()

def is_admin(chat_id, uid):
    data = load_data()
    gid = str(chat_id)
    if uid == SUDO_ID:
        return True
    if str(uid) in data.get("admins", {}).get(gid, []):
        return True
    try:
        member = bot.get_chat_member(chat_id, uid)
        return member.status in ["administrator", "creator"]
    except:
        return False

print("✅ [1] سیستم اصلی بارگذاری شد.")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data()
    gid = str(m.chat.id)
    if not data["welcome"][gid]["enabled"]:
        return
    for u in m.new_chat_members:
        bot.send_message(
            m.chat.id,
            f"👋 سلام {u.first_name}!\nبه گروه {m.chat.title} خوش اومدی 🌸\n⏰ {now_time()}"
        )

# ================= 🔒 قفل‌ها =================
@bot.message_handler(func=lambda m: cmd(m).startswith("قفل "))
def lock_system(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    gid = str(m.chat.id)
    text = cmd(m).replace("قفل ", "").strip()

    if text not in ["لینک", "گروه"]:
        return bot.reply_to(m, "⚠️ قفل نامعتبر است (فقط لینک یا گروه).")

    if text == "لینک":
        data["locks"].setdefault(gid, {"link": False, "group": False})
        data["locks"][gid]["link"] = True
        save_data(data)
        return bot.reply_to(m, "🔒 قفل لینک فعال شد ✅")

    if text == "گروه":
        try:
            perms = types.ChatPermissions(can_send_messages=False)
            bot.set_chat_permissions(m.chat.id, perms)
            bot.reply_to(m, "🚫 گروه بسته شد (فقط مدیران مجازند).")
        except:
            bot.reply_to(m, "⚠️ خطا در بستن گروه (احتمالاً ادمین نیستم).")

@bot.message_handler(func=lambda m: cmd(m).startswith("بازکردن "))
def unlock_system(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    gid = str(m.chat.id)
    text = cmd(m).replace("بازکردن ", "").strip()

    if text == "لینک":
        data["locks"][gid]["link"] = False
        save_data(data)
        return bot.reply_to(m, "🔓 قفل لینک غیرفعال شد ✅")

    if text == "گروه":
        try:
            perms = types.ChatPermissions(can_send_messages=True)
            bot.set_chat_permissions(m.chat.id, perms)
            bot.reply_to(m, "✅ گروه باز شد، همه می‌تونن پیام بدن.")
        except:
            bot.reply_to(m, "⚠️ خطا در بازکردن گروه.")

# حذف پیام‌های دارای لینک در صورت قفل بودن
@bot.message_handler(func=lambda m: True, content_types=["text"])
def link_filter(m):
    data = load_data()
    gid = str(m.chat.id)
    locks = data.get("locks", {}).get(gid, {})
    if not locks or is_admin(m.chat.id, m.from_user.id):
        return

    if locks.get("link") and re.search(r"(https?://|t\.me|telegram\.me)", m.text.lower()):
        try:
            bot.delete_message(m.chat.id, m.id)
            warn = bot.send_message(
                m.chat.id,
                f"🚫 ارسال لینک در این گروه ممنوع است!\n👤 {m.from_user.first_name}",
            )
            time.sleep(3)
            bot.delete_message(m.chat.id, warn.id)
        except:
            pass

# ================= 🚫 بن و خوشامد =================
@bot.message_handler(func=lambda m: cmd(m).startswith("بن"))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    if not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام کاربر ریپلای کن.")
    target = m.reply_to_message.from_user.id
    if is_admin(m.chat.id, target):
        return bot.reply_to(m, "❌ نمی‌تونی مدیر رو بن کنی.")
    try:
        bot.ban_chat_member(m.chat.id, target)
        bot.reply_to(m, f"🚫 کاربر {m.reply_to_message.from_user.first_name} بن شد.")
    except:
        bot.reply_to(m, "⚠️ نتونستم کاربر رو بن کنم (احتمالاً دسترسی ندارم).")

@bot.message_handler(func=lambda m: cmd(m).startswith("خوشامد "))
def toggle_welcome(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return
    data = load_data()
    gid = str(m.chat.id)
    text = cmd(m).replace("خوشامد ", "").strip()
    if text == "روشن":
        data["welcome"][gid]["enabled"] = True
        save_data(data)
        bot.reply_to(m, "👋 خوشامد فعال شد ✅")
    elif text == "خاموش":
        data["welcome"][gid]["enabled"] = False
        save_data(data)
        bot.reply_to(m, "🚫 خوشامد خاموش شد ❌")
    else:
        bot.reply_to(m, "⚠️ دستور اشتباه است. (مثلاً: خوشامد روشن)")

# ================= 🧾 آمار و ساعت =================
@bot.message_handler(func=lambda m: cmd(m) == "آمار")
def stats(m):
    data = load_data()
    groups = len(data.get("locks", {}))
    bot.reply_to(m, f"📊 آمار ربات:\n👥 گروه‌ها: {groups}\n⏰ {now_time()}")

@bot.message_handler(func=lambda m: cmd(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {now_time()} | 📅 {now_date()}")

# ================= 🚀 شروع =================
print("✅ ربات با موفقیت راه‌اندازی شد.")
bot.infinity_polling()
