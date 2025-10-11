# -*- coding: utf-8 -*-
# Persian Lux Panel - Render/GitHub ready (Enhanced, Persian commands)
# Author: adapted for Mohammad 👑
# Usage:
# - Put BOT_TOKEN and SUDO_ID in environment variables.
# - Deploy as worker (Procfile: worker: python bot.py) on Render.

import os
import json
import time
import logging
import jdatetime
import sys
from functools import wraps

import telebot
from telebot import types, apihelper
from telebot.apihelper import ApiTelegramException

# ---------- تنظیمات لاگ ----------
LOG_FILE = "error.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------- پیکربندی پایه ----------
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("⚠️ خطا: متغیر محیطی BOT_TOKEN پیدا نشد.")
    sys.exit(1)

SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"
LOCK_FILE = "instance.lock"   # فایل قفل محلی برای اطلاع (کمکی)

# ---------- دادهٔ پایه ----------
def base_data():
    return {
        "welcome": {},      # gid -> dict
        "locks": {},        # gid -> {link:False,...}
        "admins": {},       # gid -> [ids]
        "sudo_list": [],    # extra sudo ids
        "banned": {},       # gid -> [ids]
        "muted": {},        # gid -> [ids]
        "warns": {},        # gid -> {uid:count}
        "users": [],        # all users seen
        "filters": {},      # gid -> [words]
        "paused": False     # global pause (stop responders)
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error("load_data error: %s", e)
        data = base_data()
    # تضمین کلیدها
    bd = base_data()
    for k in bd:
        if k not in data:
            data[k] = bd[k]
    save_data(data)
    return data

def save_data(d):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("save_data error: %s", e)

# ---------- ابزارها ----------
def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def text_of(m):
    return (getattr(m, "text", None) or "").strip()

def cmd_lower(m):
    return text_of(m).lower()

def is_sudo(uid):
    d = load_data()
    return str(uid) == str(SUDO_ID) or str(uid) in [str(x) for x in d.get("sudo_list", [])]

def is_admin(chat_id, uid):
    d = load_data()
    if is_sudo(uid):
        return True
    gid = str(chat_id)
    if str(uid) in d.get("admins", {}).get(gid, []):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("creator", "administrator")
    except Exception:
        return False

def sudo_only(func):
    @wraps(func)
    def wrapper(m, *a, **k):
        if not is_sudo(m.from_user.id):
            return
        return func(m, *a, **k)
    return wrapper

def admin_only(func):
    @wraps(func)
    def wrapper(m, *a, **k):
        if not is_admin(m.chat.id, m.from_user.id):
            return
        return func(m, *a, **k)
    return wrapper

def register_group(gid):
    d = load_data()
    gid = str(gid)
    d["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None})
    d["locks"].setdefault(gid, {k: False for k in ["link","photo","video","sticker","gif","file","music","voice","forward","text"]})
    save_data(d)

# ---------- نمایش وضعیت پایه ----------
print("✅ سیستم پایه بارگذاری شد.")

# ---------- مدیریت ورود کاربران ----------
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    d = load_data()
    if d.get("paused"):
        return
    gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True, "type": "text", "content": None})
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    group_name = m.chat.title or "گروه"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{group_name}</b> خوش آمدی 🌸\n⏰ {shamsi_time()}"
    try:
        bot.send_message(m.chat.id, text, parse_mode="HTML")
    except Exception as e:
        logging.error("welcome_new error: %s", e)

# ---------- دستورها (تمام فارسی) ----------
@bot.message_handler(func=lambda m: cmd_lower(m) in ["دستورها","دستورات","/help","help"])
def show_help(m):
    d = load_data()
    if d.get("paused"):
        return
    txt = (
        "📚 <b>دستورات ربات (فارسی)</b>\n\n"
        "🔹 مدیریت:\n"
        "• addadmin <reply یا id> — افزودن مدیر\n"
        "• deladmin <reply یا id> — حذف مدیر\n"
        "• admins — نمایش مدیران\n"
        "• addsudo <reply یا id> — افزودن سودو (مالک)\n"
        "• delsudo <reply یا id> — حذف سودو\n"
        "• sudolist — لیست سودوها\n\n"
        "🔹 قفل‌ها (lock/unlock):\n"
        "• lock link — قفل لینک\n"
        "• lock photo / lock video / lock sticker / lock gif / lock file / lock voice / lock forward / lock text\n        • unlock ... — بازکردن\n\n"
        "🔹 مجازات:\n"
        "• ban <reply یا id> — بن کردن\n"
        "• unban <reply یا id> — آنبن\n"
        "• mute <reply یا id> — سایلنت\n"
        "• unmute <reply یا id> — برداشتن سایلنت\n"
        "• warn <reply یا id> — اخطار (3 اخطار => بن)\n\n"
        "🔹 فیلترها:\n"
        "• addfilter متن — اضافه کردن کلمهٔ فیلتر\n"
        "• delfilter متن — حذف فیلتر\n"
        "• filterlist — نمایش فیلترها\n\n"
        "🔹 ابزار:\n"
        "• id — نمایش آیدی شما\n"
        "• stats — آمار ربات (مدیران و سودوها)\n"
        "• time — ساعت شمس\n\n"
        "🔹 مدیریت ربات در سرور:\n"
        "• /pause — توقف پاسخگویی (فقط سودو)\n"
        "• /resume — ادامه کار (فقط سودو)\n"
        "• /suspend — معلق کردن سرویس (در هاست اگر لازم)\n\n"
        "برای جزئیات هر دستور، از همان دستور با / استفاده کنید."
    )
    try:
        bot.reply_to(m, txt, parse_mode="HTML")
    except Exception as e:
        logging.error("show_help error: %s", e)

# ---------- pause / resume (کنترل هنگام deploy یا ویرایش) ----------
@bot.message_handler(commands=["pause"])
@sudo_only
def pause_bot(m):
    d = load_data()
    d["paused"] = True
    save_data(d)
    bot.reply_to(m, "⏸️ ربات متوقف شد (paused). حالا پیام‌ها را پردازش نمی‌کند.")

@bot.message_handler(commands=["resume"])
@sudo_only
def resume_bot(m):
    d = load_data()
    d["paused"] = False
    save_data(d)
    bot.reply_to(m, "▶️ ربات فعال شد (resume).")

# ---------- مدیران و سودو ----------
@bot.message_handler(func=lambda m: cmd_lower(m).startswith("addsudo") or cmd_lower(m).startswith("/addsudo"))
def add_sudo(m):
    if not is_sudo(m.from_user.id):
        return
    parts = cmd_lower(m).split()
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        target = int(parts[1])
    else:
        return bot.reply_to(m, "⚠️ آیدی نفر را بفرست یا روی پیام ریپلای کن.")
    d = load_data()
    if str(target) not in d["sudo_list"]:
        d["sudo_list"].append(str(target))
        save_data(d)
        bot.reply_to(m, f"👑 {target} به لیست سودو اضافه شد.")
    else:
        bot.reply_to(m, "ℹ️ قبلاً اضافه شده بود.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("delsudo") or cmd_lower(m).startswith("/delsudo"))
def del_sudo(m):
    if not is_sudo(m.from_user.id):
        return
    parts = cmd_lower(m).split()
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    elif len(parts) > 1 and parts[1].isdigit():
        target = int(parts[1])
    else:
        return bot.reply_to(m, "⚠️ آیدی نفر را بفرست یا روی پیام ریپلای کن.")
    d = load_data()
    if str(target) in d["sudo_list"]:
        d["sudo_list"].remove(str(target))
        save_data(d)
        bot.reply_to(m, f"🗑️ {target} از سودوها حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر سودو نیست.")

@bot.message_handler(func=lambda m: cmd_lower(m) in ["sudolist","/sudolist"])
def list_sudos(m):
    d = load_data()
    lst = d.get("sudo_list", [])
    if not lst:
        return bot.reply_to(m, "👑 لیست سودوها خالی است.")
    bot.reply_to(m, "👑 سودوها:\n" + "\n".join(lst))

# ---------- افزودن / حذف مدیر ----------
@bot.message_handler(func=lambda m: cmd_lower(m).startswith("addadmin") or cmd_lower(m).startswith("/addadmin"))
@admin_only
def add_admin(m):
    d = load_data()
    gid = str(m.chat.id)
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    else:
        parts = cmd_lower(m).split()
        if len(parts) < 2 or not parts[1].isdigit():
            return bot.reply_to(m, "⚠️ آیدی عددی بفرست یا روی پیام ریپلای کن.")
        target = int(parts[1])
    d["admins"].setdefault(gid, [])
    if str(target) in d["admins"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر قبلاً مدیر شده.")
    d["admins"][gid].append(str(target))
    save_data(d)
    bot.reply_to(m, f"👮 کاربر {target} مدیر شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("deladmin") or cmd_lower(m).startswith("/deladmin"))
@admin_only
def del_admin(m):
    d = load_data()
    gid = str(m.chat.id)
    if m.reply_to_message:
        target = m.reply_to_message.from_user.id
    else:
        parts = cmd_lower(m).split()
        if len(parts) < 2 or not parts[1].isdigit():
            return bot.reply_to(m, "⚠️ آیدی عددی بفرست یا روی پیام ریپلای کن.")
        target = int(parts[1])
    if str(target) not in d.get("admins", {}).get(gid, []):
        return bot.reply_to(m, "❌ این کاربر مدیر نیست.")
    d["admins"][gid].remove(str(target))
    save_data(d)
    bot.reply_to(m, f"🗑️ مدیر {target} حذف شد.")

@bot.message_handler(func=lambda m: cmd_lower(m) in ["admins","/admins"])
def list_admins(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("admins", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "👮 لیست مدیران خالی است.")
    bot.reply_to(m, "👮 مدیران:\n" + "\n".join(lst))

# ---------- قفل‌ها (lock/unlock) ----------
LOCK_MAP = {
    "link":"link","photo":"photo","video":"video","sticker":"sticker",
    "gif":"gif","file":"file","music":"music","voice":"voice","forward":"forward","text":"text"
}

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("lock ") or cmd_lower(m).startswith("/lock "))
@admin_only
def lock_command(m):
    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_lower(m).split()
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال: lock link")
    key = parts[1]
    if key not in LOCK_MAP:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    d["locks"].setdefault(gid, {k:False for k in LOCK_MAP.values()})
    d["locks"][gid][LOCK_MAP[key]] = True
    save_data(d)
    bot.reply_to(m, f"🔒 قفل {key} فعال شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("unlock ") or cmd_lower(m).startswith("/unlock "))
@admin_only
def unlock_command(m):
    d = load_data()
    gid = str(m.chat.id)
    parts = cmd_lower(m).split()
    if len(parts) < 2:
        return bot.reply_to(m, "⚠️ مثال: unlock link")
    key = parts[1]
    if key not in LOCK_MAP:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    d["locks"].setdefault(gid, {k:False for k in LOCK_MAP.values()})
    d["locks"][gid][LOCK_MAP[key]] = False
    save_data(d)
    bot.reply_to(m, f"🔓 قفل {key} غیرفعال شد.")

# ---------- سیستم حذف خودکار (قوانین قفل‌ها) ----------
@bot.message_handler(content_types=["text","photo","video","sticker","animation","document","audio","voice","forward"])
def filters_and_locks(m):
    d = load_data()
    if d.get("paused"):
        return
    gid = str(m.chat.id)
    locks = d.get("locks", {}).get(gid, {})
    if not locks:
        return
    # نادیده گرفتن مدیران
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id):
        return
    # تبدیل متن برای بررسی لینک/فیلتر
    text = (getattr(m, "text", "") or "").lower()
    # بررسی لینک
    if locks.get("link") and text and any(x in text for x in ["http","www.","t.me/","telegram.me/"]):
        try:
            bot.delete_message(m.chat.id, m.id)
        except:
            pass
        warn = bot.send_message(m.chat.id, f"🚫 ارسال لینک ممنوع است، {m.from_user.first_name}!")
        time.sleep(3)
        try:
            bot.delete_message(m.chat.id, warn.id)
        except:
            pass
        return
    # نوع محتواها
    ct = m.content_type
    if locks.get("photo") and ct == "photo":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("video") and ct == "video":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("sticker") and ct == "sticker":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("gif") and ct == "animation":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("file") and ct == "document":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("music") and ct == "audio":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("voice") and ct == "voice":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("forward") and (m.forward_from or m.forward_from_chat):
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    if locks.get("text") and ct == "text":
        try: bot.delete_message(m.chat.id, m.id)
        except: pass
        return
    # فیلتر کلمات
    filters = d.get("filters", {}).get(gid, [])
    if filters and text:
        for w in filters:
            if w in text:
                try: bot.delete_message(m.chat.id, m.id)
                except: pass
                warn = bot.send_message(m.chat.id, f"🚫 کلمهٔ «{w}» در این گروه فیلتر است.")
                time.sleep(2)
                try: bot.delete_message(m.chat.id, warn.id)
                except: pass
                return

# ---------- فیلترها افزودن/حذف/لیست ----------
@bot.message_handler(func=lambda m: cmd_lower(m).startswith("addfilter") or cmd_lower(m).startswith("/addfilter"))
@admin_only
def add_filter(m):
    parts = cmd_lower(m).split(" ",1)
    if len(parts) < 2 or not parts[1].strip():
        return bot.reply_to(m, "⚠️ مثال: addfilter فحش")
    gid = str(m.chat.id)
    d = load_data()
    d["filters"].setdefault(gid, [])
    word = parts[1].strip()
    if word in d["filters"][gid]:
        return bot.reply_to(m, "ℹ️ این کلمه قبلاً فیلتر شده.")
    d["filters"][gid].append(word)
    save_data(d)
    bot.reply_to(m, f"✅ کلمه «{word}» فیلتر شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("delfilter") or cmd_lower(m).startswith("/delfilter"))
@admin_only
def del_filter(m):
    parts = cmd_lower(m).split(" ",1)
    if len(parts) < 2 or not parts[1].strip():
        return bot.reply_to(m, "⚠️ مثال: delfilter فحش")
    gid = str(m.chat.id)
    d = load_data()
    word = parts[1].strip()
    if word not in d.get("filters", {}).get(gid, []):
        return bot.reply_to(m, "❌ این کلمه در فیلتر نیست.")
    d["filters"][gid].remove(word)
    save_data(d)
    bot.reply_to(m, f"✅ کلمه «{word}» از فیلتر حذف شد.")

@bot.message_handler(func=lambda m: cmd_lower(m) in ["filterlist","/filterlist"])
def list_filters_cmd(m):
    d = load_data()
    gid = str(m.chat.id)
    lst = d.get("filters", {}).get(gid, [])
    if not lst:
        return bot.reply_to(m, "🔍 هیچ فیلتری تعریف نشده.")
    bot.reply_to(m, "🚫 کلمات فیلترشده:\n" + "\n".join(lst))

# ---------- بن / آنبن / سایلنت ----------
def parse_target_from(m):
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    parts = text_of(m).split()
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("ban") or cmd_lower(m).startswith("/ban"))
@admin_only
def ban_user(m):
    if not bot_can_restrict := True:
        pass
    target = parse_target_from(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام فرد ریپلای کن یا آیدی عددی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "❌ نمی‌توان مدیر/سودو را بن کرد.")
    d = load_data()
    gid = str(m.chat.id)
    d["banned"].setdefault(gid, [])
    if target in d["banned"][gid]:
        return bot.reply_to(m, "ℹ️ این شخص قبلاً بن شده.")
    d["banned"][gid].append(target)
    save_data(d)
    try:
        bot.ban_chat_member(m.chat.id, target)
    except Exception as e:
        logging.error("ban_user error: %s", e)
        return bot.reply_to(m, "⚠️ من دسترسی بن کردن ندارم.")
    bot.reply_to(m, f"🚫 کاربر {target} بن شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("unban") or cmd_lower(m).startswith("/unban"))
@admin_only
def unban_user(m):
    target = parse_target_from(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام فرد ریپلای کن یا آیدی عددی بده.")
    d = load_data()
    gid = str(m.chat.id)
    if target not in d.get("banned", {}).get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر بن نیست.")
    d["banned"][gid].remove(target)
    save_data(d)
    try:
        bot.unban_chat_member(m.chat.id, target)
    except Exception:
        pass
    bot.reply_to(m, f"✅ کاربر {target} آنبن شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("mute") or cmd_lower(m).startswith("/mute"))
@admin_only
def mute_user(m):
    target = parse_target_from(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام فرد ریپلای کن یا آیدی عددی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "❌ نمی‌شود مدیر یا سودو را سایلنت کرد.")
    d = load_data()
    gid = str(m.chat.id)
    d["muted"].setdefault(gid, [])
    if target in d["muted"][gid]:
        return bot.reply_to(m, "ℹ️ این شخص قبلاً سایلنت شده.")
    d["muted"][gid].append(target)
    save_data(d)
    try:
        bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=False))
    except Exception:
        pass
    bot.reply_to(m, f"🔇 کاربر {target} سایلنت شد.")

@bot.message_handler(func=lambda m: cmd_lower(m).startswith("unmute") or cmd_lower(m).startswith("/unmute"))
@admin_only
def unmute_user(m):
    target = parse_target_from(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام فرد ریپلای کن یا آیدی عددی بده.")
    d = load_data()
    gid = str(m.chat.id)
    if target not in d.get("muted", {}).get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر سایلنت نیست.")
    d["muted"][gid].remove(target)
    save_data(d)
    try:
        bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=True))
    except Exception:
        pass
    bot.reply_to(m, f"🔊 کاربر {target} آزاد شد.")

# ---------- اخطار / warns ----------
@bot.message_handler(func=lambda m: cmd_lower(m).startswith("warn") or cmd_lower(m).startswith("/warn"))
@admin_only
def warn_user(m):
    target = parse_target_from(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام فرد ریپلای کن یا آیدی عددی بده.")
    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "❌ نمی‌توان به مدیر یا سودو اخطار داد.")
    d = load_data()
    gid = str(m.chat.id)
    d["warns"].setdefault(gid, {})
    key = str(target)
    d["warns"][gid][key] = d["warns"][gid].get(key, 0) + 1
    count = d["warns"][gid][key]
    save_data(d)
    text = f"⚠️ کاربر {target} اخطار شماره {count} دریافت کرد."
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, target)
            text += "\n🚫 به دلیل ۳ اخطار بن شد."
        
