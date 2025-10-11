# ================= 🚫 سیستم بن، میوت، و اخطار =================

def bot_can_restrict(m):
    try:
        me = bot.get_me()
        perms = bot.get_chat_member(m.chat.id, me.id)
        if perms.status in ("administrator", "creator") and getattr(perms, "can_restrict_members", True):
            return True
    except:
        pass
    bot.reply_to(m, "⚠️ من ادمین نیستم یا اجازه‌ی محدود کردن کاربران را ندارم.")
    return False

def target_user(m):
    if m.reply_to_message:
        return m.reply_to_message.from_user.id
    parts = cmd_text(m).split()
    if len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return None

# 🚫 بن کاربر
@bot.message_handler(func=lambda m: cmd_text(m).startswith("بن "))
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند بن کنند.")
    if not bot_can_restrict(m):
        return

    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام کاربر ریپلای کن یا آیدی عددی بده.")

    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌توانی مدیر یا سودو را بن کنی!")

    d = load_data()
    gid = str(m.chat.id)
    d["banned"].setdefault(gid, [])
    if target in d["banned"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل بن شده است.")
    d["banned"][gid].append(target)
    save_data(d)

    try:
        bot.ban_chat_member(m.chat.id, target)
        bot.send_message(m.chat.id, f"🚫 کاربر <a href='tg://user?id={target}'>بن</a> شد ❌", parse_mode="HTML")
    except:
        bot.reply_to(m, "⚠️ دسترسی لازم برای بن کردن را ندارم.")

# ✅ آزاد کردن از بن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("آزاد "))
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند آزاد کنند.")
    if not bot_can_restrict(m):
        return

    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")

    d = load_data()
    gid = str(m.chat.id)
    if target not in d["banned"].get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر بن نیست.")
    d["banned"][gid].remove(target)
    save_data(d)

    bot.unban_chat_member(m.chat.id, target)
    bot.send_message(m.chat.id, "✅ کاربر از بن آزاد شد 🌸")

# 🔇 ساکت کردن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("ساکت "))
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند ساکت کنند.")
    if not bot_can_restrict(m):
        return

    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ روی پیام کاربر ریپلای کن یا آیدی بده.")

    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌توانی مدیر یا سودو را ساکت کنی!")

    d = load_data()
    gid = str(m.chat.id)
    d["muted"].setdefault(gid, [])
    if target in d["muted"][gid]:
        return bot.reply_to(m, "ℹ️ این کاربر از قبل ساکت بوده.")
    d["muted"][gid].append(target)
    save_data(d)

    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=False))
    bot.send_message(m.chat.id, f"🔇 کاربر <a href='tg://user?id={target}'>ساکت</a> شد 💬", parse_mode="HTML")

# 🔊 آزاد کردن از سکوت
@bot.message_handler(func=lambda m: cmd_text(m).startswith("بازکردن سکوت"))
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند سکوت را بردارند.")
    if not bot_can_restrict(m):
        return

    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای کن یا آیدی بده.")

    d = load_data()
    gid = str(m.chat.id)
    if target not in d["muted"].get(gid, []):
        return bot.reply_to(m, "ℹ️ این کاربر در سکوت نیست.")
    d["muted"][gid].remove(target)
    save_data(d)

    bot.restrict_chat_member(m.chat.id, target, permissions=types.ChatPermissions(can_send_messages=True))
    bot.send_message(m.chat.id, "🔊 سکوت از کاربر برداشته شد 🌼", parse_mode="HTML")

# ⚠️ اخطار دادن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("اخطار "))
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id):
        return

    target = target_user(m)
    if not target:
        return bot.reply_to(m, "⚠️ ریپلای یا آیدی بده.")

    if is_admin(m.chat.id, target) or is_sudo(target):
        return bot.reply_to(m, "😎 نمی‌توانی به سودو یا مدیر اخطار بدهی!")

    d = load_data()
    gid = str(m.chat.id)
    d["warns"].setdefault(gid, {})
    count = d["warns"][gid].get(str(target), 0) + 1
    d["warns"][gid][str(target)] = count
    save_data(d)

    msg = f"⚠️ کاربر اخطار شماره <b>{count}</b> دریافت کرد."
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, target)
            msg += "\n🚫 به دلیل ۳ اخطار بن شد."
            d["warns"][gid][str(target)] = 0
            save_data(d)
        except:
            msg += "\n⚠️ نتوانستم بن کنم (دسترسی محدود است)."

    bot.send_message(m.chat.id, msg, parse_mode="HTML")
