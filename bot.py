import logging
import datetime
import requests
import json
import asyncio
import os
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
)

# ========= CONFIG =========
BOT_TOKEN = "7833301238:AAGQUjgOGgRb8ueInaIAGRjfLdAB5KdUtYY"
OWNER = "<@cosmos_1oo7>"  # example: "@NR_CODEX"
API_URL = "https://android-likeapi.vercel.app/like?uid={uid}&server_name=ag"
WEBHOOK_URL = "<your_webhook_url_here>"
PORT = int(os.environ.get("PORT", 5000))
ADMIN_IDS = [7549258335]  # example: [123456789]
ALLOWED_GROUPS = {-1002564578124}  # example: {-1001234567890}
vip_users = {7549258335}
DEFAULT_DAILY_LIMIT = 100

# ========= STATE =========
allowed_groups = set(ALLOWED_GROUPS)
group_usage = {}
group_limits = {}
last_reset_date = {}
user_data = {}
promotion_message = ""
command_enabled = True

# ========= LOGGING =========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Log initial state
logger.info(f"Initialized ADMIN_IDS: {ADMIN_IDS}")
logger.info(f"Initialized ALLOWED_GROUPS: {ALLOWED_GROUPS}")
logger.info(f"Initialized vip_users: {vip_users}")

# ========= HELPERS =========
async def get_user_name(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        user = await context.bot.get_chat(user_id)
        return user.full_name or f"User {user_id}"
    except Exception as e:
        logger.error(f"Muammo🤷🏻‍♂️! Foydalanuvchi topilmadi {user_id}: {e}")
        return f"User {user_id}"

def is_group(update: Update):
    return update.message.chat.type in ["group", "supergroup"]

def get_today():
    return datetime.date.today().strftime("%Y-%m-%d")

def reset_if_needed(group_id: int):
    today = datetime.date.today()
    if last_reset_date.get(group_id) != today:
        group_usage[group_id] = 0
        last_reset_date[group_id] = today

def get_limit(group_id: int):
    return group_limits.get(group_id, DEFAULT_DAILY_LIMIT)

def check_command_enabled(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not command_enabled and update.message.text != "/on":
            await update.message.reply_text("🚫 Buyruqlar hozircha cheklangan!")
            logger.info(f"❌ Bu foydalanuvchi uchun cheklangan! {update.effective_user.id}")
            return
        return await func(update, context)
    return wrapper

async def check_group_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group(update):
        return True
    group_id = update.effective_chat.id
    logger.info(f"Bu chat uchun ruxsat tekshirilmoqda... group_id: {group_id}, allowed_groups: {allowed_groups}")
    if group_id not in allowed_groups:
        await update.message.reply_text(
            "🚫 Bu bot faqat ushbu guruh uchun yaratilgan: t.me/GarenaLikeServer\n📞 Iltmos owner bilan bogʻlaning @cosmos_1oo7"
        )
        logger.warning(f"🏴‍☠️ Botdan ruxsatsiz ushbu guruh orqali foydalanildi: {group_id}")
        return False
    return True

# ========= CORE COMMANDS =========
@check_command_enabled
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    logger.info(f"Received /start from user {update.effective_user.id}")
    await update.message.reply_text("👋 Assalomu alaykum mijoz! /like sg 12345678 koʻrinishida komanda yuborib, akauntingizga har 24 soatda 100 ta like yuborishingiz mumkin!")

@check_command_enabled
async def gay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    await update.message.reply_text("Geyligingni bilardim 🫵🏿🌚")

@check_command_enabled
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    help_text = """
📘 HELP MENU

🔹 Like joʻnatish, maʼlumot olish:
/like <region> <uid> - Like lar joʻnatish
/check - Mening limitim...
/groupstatus - Guruh statusi
/remain - Bugun uchun Like lar
/gay - Bosma buni (bosgan toʻt)🤧

🔹 Oddiy foydalanuvchilar uchun:
/userinfo <user_id> - Akkaunt haqida maʼlumotlar olish
/stats - Bot statistikasi
/feedback - malumot olish

🔹 Bot faolligi:
/status - Bot statusi
/on - Botni yoqish (Admin uchun)
/off - Botni oʻchirish (Admin uchun)

👑 Owner: {@cosmos_1oo7}
"""
    await update.message.reply_text(help_text)

@check_command_enabled
async def open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Received /open from user {user_id}, ADMIN_IDS: {ADMIN_IDS}")
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        logger.warning(f"🏴‍☠️ Tasdiqlanmagan akkaunt /open komandasini bajarishga urindi {user_id}")
        return
    admin_menu = """
📘 HUQUQLAR

🔹 Admin huquqlari:
/allow <group_id> - Botni biron guruhda ishlaydigan qilish
/remove <group_id> - Botni biron guruhda ishlamaydigan qilish
/setremain <number> - Guruh uchun limit kiritish
/groupreset - Guruh limitini asliga qaytarish
/broadcast <msg> - Global tarmoqqa ulanish
/send <msg> - VIP yoki guruh qoʻshish
/setadmin [user_id] yoki xabarga reply qiling
/removeadmin [user_id] yoli xabarga reply qiling
/adminlist - Barcha adminlarni koʻrish

🔹 VIP huquqlari:
/setvip <user_id> - VIP qoʻshish
/removevip <user_id> - VIP olib tashlash
/viplist - Barcha VIPlarni koʻrish
/setpromotion <text> - promokod?

🔹 Botni oʻchirish/yoqish:
/on - Yoqish
/off - Oʻchirish
"""
    await update.message.reply_text(admin_menu)

# ========= BROADCAST COMMANDS =========
@check_command_enabled
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Ushbu komandani ishlating!: /broadcast")
        return
    text = " ".join(context.args)
    sent = 0
    failed = 0
    msg = await update.message.reply_text("📢 Jarayon boshlanmoqda...")
    for user_id in set(user_data.keys()):
        try:
            await context.bot.send_message(user_id, text)
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Error broadcasting to user {user_id}: {e}")
        await asyncio.sleep(0.1)
    for group_id in allowed_groups:
        try:
            await context.bot.send_message(group_id, text)
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"🤷🏻‍♂️ Bu guruh uchun bot sozlanmagan! {group_id}: {e}")
        await asyncio.sleep(0.1)
    await msg.edit_text(f"📢 Jarayon yakunlandi!\n\n✅ Sent: {sent}\n❌ Nimadir xato ketdi!: {failed}")

@check_command_enabled
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in vip_users:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Botdan to'liq foydalanish uchun botga adminlik bering.")
        return
    success_users = []
    success_groups = []
    failed_users = []
    failed_groups = []
    for user_id in set(vip_users):
        try:
            user = await context.bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user.full_name
            await context.bot.send_message(user_id, text)
            success_users.append(f"{username} (ID: {user_id})")
        except Exception as e:
            failed_users.append(f"User {user_id}")
            logger.error(f"🤷🏻‍♂️ VIP qoʻshishda muammo {user_id}: {e}")
    for group_id in set(allowed_groups):
        try:
            chat = await context.bot.get_chat(group_id)
            group_name = chat.title or f"Guruh {group_id}"
            await context.bot.send_message(group_id, text)
            success_groups.append(f"{group_name} (ID: {group_id})")
        except Exception as e:
            failed_groups.append(f"Guruh {group_id}")
            logger.error(f"Guruhga joʻnatishda muammo! {group_id}: {e}")
    response = "📢 Xabar olindi\n\n"
    if success_users:
        response += f"✅ Muvaffaqiyatli joʻnatilgan, {len(success_users)} foydalanuvchilar:\n" + "\n".join(success_users) + "\n\n"
    if success_groups:
        response += f"✅ Muvaffaqiyatli joʻnatilgan, {len(success_groups)} guruhlar:\n" + "\n".join(success_groups) + "\n\n"
    if failed_users:
        response += f"❌ Muvaffaqiyatsiz urinish, {len(failed_users)} foydalanuvchlar:\n" + "\n".join(failed_users) + "\n\n"
    if failed_groups:
        response += f"❌ Muvaffaqiyatsiz urinish, {len(failed_groups)} guruhlar:\n" + "\n".join(failed_groups)
    await update.message.reply_text(response[:4000])

# ========= ADMIN TOOLS =========
@check_command_enabled
async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    user_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else (
        int(context.args[0]) if context.args else None)
    if not user_id:
        await update.message.reply_text("⚠️ Biron xabarga reply qiling yoki foydalanuvchi_id(12427910) kabi yozing")
        return
    try:
        user = await context.bot.get_chat(user_id)
        is_vip = "✅" if user_id in vip_users else "❌"
        is_admin = "✅" if user_id in ADMIN_IDS else "❌"
        await update.message.reply_text(
            f"👤 Foydalanuvchi ma'lumotlari\n\n"
            f"🆔 ID: {user.id}\n"
            f"📛 Nik: {user.full_name}\n"
            f"🔗 Username: @{user.username if user.username else 'N/A'}\n"
            f"👑 VIP: {is_vip}\n"
            f"🛡️ Admin: {is_admin}\n"
            f"📅 Oxirgi aktivlik: {user_data.get(user_id, {}).get('date', 'Never')}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

@check_command_enabled
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    today = get_today()
    active_users = sum(1 for data in user_data.values() if data.get('date') == today)
    await update.message.reply_text(
        f"📊 Bot Statusi\n\n"
        f"👥 Barcha foydalanuvchilar: {len(user_data)}\n"
        f"📅 Bugun uchun aktiv: {active_users}\n"
        f"👑 VIP foydalanuvchilar: {len(vip_users)}\n"
        f"🛡️ Adminlar: {len(ADMIN_IDS)}\n"
        f"💬 Tasdiqlangan guruhlar roʻyxati: {len(allowed_groups)}\n"
        f"⏰ Oxirgi yangilanish(24soat): {last_reset_date.get('last', 'Never')}"
    )

@check_command_enabled
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    today = datetime.date.today().strftime("%Y-%m-%d")
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    daily_users = {}
    for data in user_data.values():
        date = data.get('date')
        if date:
            daily_users[date] = daily_users.get(date, 0) + 1
    await update.message.reply_text(
        f"📈 Statistika\n\n"
        f"📅 Bugun: {daily_users.get(today, 0)} users\n"
        f"📅 Oxirgi 7 kun: {sum(count for date, count in daily_users.items() if date >= week_ago)}\n"
        f"📅 Har doim: {len(user_data)} users\n"
        f"👑 VIP foydalanuvchilar: {len(vip_users)}\n"
        f"💬 Tasdiqlangan guruhlar roʻyxati: {len(allowed_groups)}"
    )

# ========= USER COMMANDS =========
@check_command_enabled
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /feedback <your message>")
        return
    feedback_text = " ".join(context.args)
    user = update.effective_user
    feedback_msg = (
        f"📢 Yangi murojat\n\n"
        f"👤 Murojatchi: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📝 Xabar: {feedback_text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, feedback_msg)
        except Exception as e:
            logger.error(f"Murojat adminga joʻnatilmadi? Nimadir xato ketti!{admin_id}: {e}")
    await update.message.reply_text("✅ Murojatingiz qabul qilindi! Biz uni tez orada koʻrib chiqamiz!")

@check_command_enabled
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    user_id = update.effective_user.id
    today = get_today()
    user_info = user_data.get(user_id, {})
    user_date = user_info.get("date")
    count = user_info.get("count", 0)
    status = "VIP" if user_id in vip_users else (
        f"{count}/1 ✅ Ishlatildi" if user_date == today else "0/1 ❌ Ishlatilmadi"
    )
    await update.message.reply_text(
        f"👤 Hurmatli {update.effective_user.first_name}, YOUR STATUS\n\n"
        f"🎯 Ma'lumot: {status}\n"
        f"👑 OWNER: {OWNER}"
    )

@check_command_enabled
async def setpromotion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in vip_users:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    global promotion_message
    promotion_message = " ".join(context.args)
    await update.message.reply_text("✅ Promokod qabul qilindi!")

@check_command_enabled
async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    if not is_group(update):
        return
    group_id = update.effective_chat.id
    if group_id not in allowed_groups:
        return
    reset_if_needed(group_id)
    used = group_usage.get(group_id, 0)
    limit = get_limit(group_id)
    if used >= limit:
        await update.message.reply_text("❌ Guruh kunlik limitga yetdi!")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("⚠️ Bot ishlatilishi: /like sg uid(12345678)")
        return
    processing_msg = await update.message.reply_text("⏳ Iltimos kuting...")
    region, uid = args
    user_id = update.effective_user.id
    today = get_today()
    is_vip = user_id in vip_users
    if not is_vip:
        user_info = user_data.get(user_id, {})
        if user_info.get("date") == today and user_info.get("count", 0) >= 1:
            await processing_msg.edit_text("🥲 Siz oxirgi 24 soat uchun limitni ishlatib boʼldingiz! 📞 Koʻproq like? @cosmos_1oo7")
            return
        user_data[user_id] = {"date": today, "count": user_info.get("count", 0)}
    try:
        api_url = API_URL.format(uid=uid, region=region)
        logger.info(f"Calling API: {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"API response for UID {uid}: {data}")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logger.error(f"ID uchun yaroqsiz javob! {uid}: Endpoint not found")
            await processing_msg.edit_text("🚨 Like server hozircha ishlamaypti (Error:API not found). Iltmos keyinroq urinib koʻring yoki batafsil maʼlumot olish uchun menga yozing: @cosmos_1oo7")
            return
        logger.error(f"Ushbu ID uchun nimadir xato ketti!? {uid}: {e}")
        await processing_msg.edit_text("🚨 API Error! Iltmos keyinroq urinib koʻring!")
        return
    except Exception as e:
        logger.error(f"Ushbu ID uchun nimadir xato ketti!? {uid}: {e}")
        await processing_msg.edit_text("🚨 API Error! Iltimos keyinroq qayta urinib koʻring!")
        return
    required_keys = ["PlayerNickname", "UID", "LikesbeforeCommand", "LikesafterCommand", "LikesGivenByAPI", "status"]
    if not all(key in data for key in required_keys):
        await processing_msg.edit_text("⚠️ ID toʻgʻri yozilganiga ishonch hosil qiling. 🙁 ID serverda topilmadi yoki nimadir xato ketti!?")
        logger.warning(f"ID uchun tugallanmagan javob? {uid}: {data}")
        return
    # Updated status check for status 1 or 2
    if data.get("status") not in [1, 2]:
        await processing_msg.edit_text(f"⚠️ Serverdan javob olishda xato!: {data.get('status')}. Iltmos keyinroq urinib koʻring yoki batafsil maʼlumot olish uchun @cosmos_1oo7")
        logger.warning(f"Invalid status {data.get('status')} for UID {uid}")
        return
    if data.get("LikesGivenByAPI") == 0 or data.get("LikesbeforeCommand") == data.get("LikesafterCommand"):
        await processing_msg.edit_text("⚠️ Ushbu ID allaqachon bugungi limitga yetdi, iltmos boshqa ID dan foydalaning yoki 24 soat kuting!")
        logger.info(f"Like lar qo'shilmadi (Error 404) {uid}: {data}")
        return
    if not is_vip:
        user_data[user_id]["count"] += 1
    group_usage[group_id] = group_usage.get(group_id, 0) + 1
    text = (
        f"✅ Like lar muvaffaqiyatli joʻnatildi! (Status: {data.get('status')})\n\n"
        f"👤 Nik: {data['PlayerNickname']}\n"
        f"🆔 ID: {data['UID']}\n"
        f"🌍 Server: {region.upper()}\n"
        f"💩 Oldin: {data['LikesbeforeCommand']}\n"
        f"☠️ Keyin: {data['LikesafterCommand']}\n"
        f"😊 Berildi: {data['LikesGivenByAPI']}\n"
        f"P:s Bizni tanlaganinhizdan mamnunmiz 🤧🌚"
    )
    if promotion_message:
        text += f"\n\n📢 {promotion_message}"
    try:
        user_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if user_photos.total_count > 0:
            photo_file = await user_photos.photos[0][-1].get_file()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_file.file_id,
                caption=text,
                reply_to_message_id=update.message.message_id
            )
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(text)
    except Exception as e:
        logger.error(f"Muammo(rasm sababli?) {user_id}: {e}")
        await processing_msg.edit_text(text)

@check_command_enabled
async def groupstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    if not is_group(update):
        return
    group_id = update.effective_chat.id
    count = group_usage.get(group_id, 0)
    await update.message.reply_text(
        f"📊 Guruh statusi\n\n"
        f"🆔 Guruh ID: {group_id}\n"
        f"✅ Bugun likelar ishlatildi: {count}/{get_limit(group_id)}\n"
        f"⏰ Qayta tiklanish: 4:30 (har kuni)"
    )

@check_command_enabled
async def remain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    today = get_today()
    used_users = [uid for uid, data in user_data.items() if data.get("date") == today]
    await update.message.reply_text(
        f"📊 Bugungi ishlatilish\n\n"
        f"✅ Like joʻnatgan foydalanuvchlar: {len(used_users)}\n"
        f"📅 Sana: {today}"
    )

@check_command_enabled
async def allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlangan komanda ishlatildi!")
        return
    if not is_group(update):
        await update.message.reply_text("⚠️ Bu komanda faqat guruh ichida ishlaydi! (Lox szu 🌚)")
        return
    try:
        gid = int(context.args[0]) if context.args else update.effective_chat.id
        allowed_groups.add(gid)
        logger.info(f"Guruh tasdiqlangan guruhlar roʻyxatiga kirdi {gid} to allowed_groups: {allowed_groups}")
        await update.message.reply_text(f"✅ Guruh {gid} tasdiqlandi.")
    except Exception as e:
        logger.error(f"Komanda bilan muammo!: {e}")
        await update.message.reply_text("⚠️ Notoʻgʻri guruh ID yoki xatolik(Error 404). /allow yoki /allow <group_id> komandalarini ishlatib koʻring.")

@check_command_enabled
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan komanda ishlatildi!")
        return
    try:
        gid = int(context.args[0])
        allowed_groups.discard(gid)
        logger.info(f"Guruh tasdiqlangan guruhlar roʻyxatidan olib tashlandi {gid} from allowed_groups: {allowed_groups}")
        await update.message.reply_text(f"❌ Guruh {gid} olib tashlandi.")
    except Exception as e:
        logger.error(f"Komandani oʻchirishda xatolik!: {e}")
        await update.message.reply_text("⚠️ Guruh ID notoʻgʻri kiritildi.")

@check_command_enabled
async def groupreset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    group_usage.clear()
    await update.message.reply_text("✅ Guruh limiti yangilandi!")

@check_command_enabled
async def setremain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan komanda ishlatildi!")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Komandani ishlating: /setremain <son>")
        return
    group_id = update.effective_chat.id
    group_limits[group_id] = int(context.args[0])
    await update.message.reply_text(f"✅ Kundalik limit: {context.args[0]} likelar.")

@check_command_enabled
async def autogroupreset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    await update.message.reply_text("✅ Guruh avtomatlashtirildi. Botni qayta yuklash vaqti(har kuni): 4:30")

@check_command_enabled
async def setvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt, siz ushbu komandadan foydalana olmaysiz!")
        return
    replied_user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    user_id = replied_user.id if replied_user else (int(context.args[0]) if context.args else None)
    if not user_id:
        await update.message.reply_text("⚠️ Ishlatish: xabarga reply qiling `/setvip` yoki ishlating: `/setvip <user_id>`")
        return
    if user_id in vip_users:
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} bu foydalanuvchi allaqachon VIP dasturida.")
    else:
        vip_users.add(user_id)
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} (ID: {user_id}) muvaffaqiyatli VIP dasturiga qoʻshildi.")

@check_command_enabled
async def removevip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt, siz ushbu komandadan foydalana olmaysiz!")
        return
    replied_user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    user_id = replied_user.id if replied_user else (int(context.args[0]) if context.args else None)
    if not user_id:
        await update.message.reply_text("⚠️ Ishlatish: xabarga reply qiling `/removevip` yoki ishlating: `/removevip <user_id>`")
        return
    if user_id in vip_users:
        vip_users.remove(user_id)
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} (ID: {user_id}) VIP dasturidn olib tashlandi.")
    else:
        await update.message.reply_text("❌ Fodalanuvchi VIP dasturida emas.")

@check_command_enabled
async def viplist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    if not vip_users:
        await update.message.reply_text("❌ Hozircha VIP dasturida xech kim yoʻq.")
        return
    vip_list = []
    for user_id in vip_users:
        name = await get_user_name(context, user_id)
        vip_list.append(f"👑 {name} (ID: {user_id})")
    await update.message.reply_text("🌟 VIP foydalanuvchilar:\n" + "\n".join(vip_list))

@check_command_enabled
async def setadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    replied_user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    user_id = update.message.reply_to_message.from_user.id if replied_user else (int(context.args[0]) if context.args else None)
    if not user_id:
        await update.message.reply_text("⚠️ Ishlatish: xabarga reply qiling: `/setadmin` yoki ishlating:`/setadmin <user_id>`")
        return
    if user_id in ADMIN_IDS:
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} foydalanuvchi allaqachon admin.")
    else:
        ADMIN_IDS.append(user_id)
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} (ID: {user_id}) foydalanuvchi adminlikka tayinlandi.")

@check_command_enabled
async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt!")
        return
    replied_user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    user_id = replied_user.id if replied_user else (int(context.args[0]) if context.args else None)
    if not user_id:
        await update.message.reply_text("⚠️ Ishlatish: xabarga reply qiling `/removeadmin` yoki ishlating: `/removeadmin <user_id>`")
        return
    if user_id in ADMIN_IDS:
        ADMIN_IDS.remove(user_id)
        name = await get_user_name(context, user_id)
        await update.message.reply_text(f"✅ {name} (ID: {user_id}) foydalanuvchi adminlikdan olib tashlandi.")
    else:
        await update.message.reply_text("❌ Foydalanuvchi admin emas.")

@check_command_enabled
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update, context):
        return
    if not ADMIN_IDS:
        await update.message.reply_text("❌ Hozircha adminlar yoʻq.")
        return
    admin_list = []
    for user_id in ADMIN_IDS:
        name = await get_user_name(context, user_id)
        admin_list.append(f"🦅 {name} (ID: {user_id})")
    await update.message.reply_text("🔐 Adminlar:\n" + "\n".join(admin_list))

@check_command_enabled
async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt, siz ushbu komandadan foydalana olmaysiz!")
        return
    global command_enabled
    command_enabled = False
    await update.message.reply_text("⛔ Komandalar oʻchirildi.")

@check_command_enabled
async def on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Tasdiqlanmagan akkaunt, siz ushbu komandadan foydalana olmaysiz!")
        return
    global command_enabled
    command_enabled = True
    await update.message.reply_text("✅ Komandalar ishga tushirildi.")

# ========= AUTO RESET TASK =========
async def reset_group_usage_task():
    while True:
        try:
            now = datetime.now()
            reset_time = now.replace(hour=4, minute=30, second=0, microsecond=0)
            if now >= reset_time:
                reset_time += datetime.timedelta(days=1)
            wait_seconds = (reset_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            group_usage.clear()
            logger.info("✅ Guruh like limit yangilanish vaqti 4:30")
        except Exception as e:
            logger.error(f"Yangilanishda muammo: {e}")
            await asyncio.sleep(60)

# ========= WEBHOOK SETUP =========
async def webhook_handler(request: web.Request):
    try:
        app = request.app['telegram_app']
        update = Update.de_json(await request.json(), app.bot)
        await app.process_update(update)
        logger.info("Webhook update processed successfully")
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return web.Response(status=500)

async def health_check(request: web.Request):
    logger.info("Health check requested")
    return web.Response(text="Bot is running", status=200)

async def set_webhook():
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

def setup_application():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gay", gay))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("open", open))
    app.add_handler(CommandHandler("like", like))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("setpromotion", setpromotion))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("groupstatus", groupstatus))
    app.add_handler(CommandHandler("remain", remain))
    app.add_handler(CommandHandler("userinfo", userinfo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("allow", allow))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("groupreset", groupreset))
    app.add_handler(CommandHandler("setremain", setremain))
    app.add_handler(CommandHandler("autogroupreset", autogroupreset))
    app.add_handler(CommandHandler("setvip", setvip))
    app.add_handler(CommandHandler("removevip", removevip))
    app.add_handler(CommandHandler("viplist", viplist))
    app.add_handler(CommandHandler("setadmin", setadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("off", off))
    app.add_handler(CommandHandler("on", on))
    return app

async def main():
    logger.info("Starting bot...")
    telegram_app = setup_application()
    web_app = web.Application()
    web_app['telegram_app'] = telegram_app
    web_app.router.add_post('/', webhook_handler)
    web_app.router.add_get('/health', health_check)
    await set_webhook()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"Webhook server running on port {PORT}")
    await telegram_app.initialize()
    telegram_app.create_task(reset_group_usage_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    if not all([BOT_TOKEN, WEBHOOK_URL]):
        logger.error("Missing required environment variables: BOT_TOKEN or WEBHOOK_URL")
        exit(1)
    asyncio.run(main())
