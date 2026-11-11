import os
import re
import uuid
import time
import shutil
import sqlite3
import logging
import tempfile
import threading

import telebot
from telebot import types
from flask import Flask
import yt_dlp

# =============== SOZLAMALAR ===============

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8019481444
BOT_USERNAME = "SavedToVid_bot"

MAX_FILE_SIZE_MB = 49
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

DB_PATH = os.getenv("DB_PATH", "bot.db")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN sozlanmagan!")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

download_lock = threading.Semaphore(2)
pending_downloads = {}
broadcast_waiting = set()
db_lock = threading.Lock()

logging.basicConfig(level=logging.INFO)

# =============== MATNLAR ===============

TEXTS = {
    "uz": {
        "choose": "🌐 Tilni tanlang:",
        "welcome": """👋 Assalomu alaykum!

🚀 SAVE VIDEO botiga xush kelibsiz!

Men ijtimoiy tarmoqlardan video yuklab beruvchi botman.

📥 QO‘LLAB-QUVVATLANADIGAN TARMOQLAR:

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 Va boshqa qo‘llab-quvvatlanadigan platformalar.

🎬 ASOSIY IMKONIYATLAR:

✅ Videolarni MP4 formatida yuklab olish.
✅ Mavjud sifat variantlarini tanlash.
✅ Havola orqali tez yuklab olish.
✅ Sodda va qulay foydalanish.

👥 GURUHLAR UCHUN MAXSUS FUNKSIYALAR:

🧹 Guruhga a'zo qo‘shilganda yoki a'zo chiqib ketganda paydo bo‘ladigan xabarlarni avtomatik o‘chiradi.

🚫 Reklama va keraksiz havolali xabarlarni o‘chiradi.

🔒 Guruhingizni tartibli saqlashga yordam beradi.

⚙️ Ushbu funksiyalar uchun botga administrator huquqi va xabarlarni o‘chirish ruxsatini bering.

➕ BOTNI GURUHINGIZGA QO‘SHING!

❤️ Bizning xizmatimizdan foydalanganingiz uchun rahmat!

📩 Video havolasini yuboring va yuklab olishni boshlang!""",
        "link": "📩 Video havolasini yuboring.",
        "working": "⏳ Video/MP4 yuklab olinmoqda...",
        "success": f"""✅ Yuklab olindi!

Yuborgan linkingiz uchun @{BOT_USERNAME} nomidan sizga rahmat! 🔥

✨ Botning qo‘shimcha funksiyalari:

👥 Guruhlarda kirdi-chiqdi xabarlarini avtomatik o‘chiradi.
🚫 Reklama va keraksiz xabarlarni o‘chirishga yordam beradi.

❤️ Biz bilan qoling!""",
        "error": "❌ Videoni yuklab bo‘lmadi. Boshqa havolani yuborib ko‘ring.",
        "youtube_error": "❗ YouTube videosini yuklab bo‘lmadi. YouTube cheklovlari yoki video sozlamalari sabab bo‘lishi mumkin.",
        "button": "🎬 Videoni yuklab olish",
        "group": "➕ Guruhga qo‘shish",
        "selected": "✅ Til o‘zgartirildi.",
        "accepted": "✅ Havola qabul qilindi:"
    },

    "ru": {
        "choose": "🌐 Выберите язык:",
        "welcome": """👋 Здравствуйте!

🚀 Добро пожаловать в SAVE VIDEO!

Я бот для скачивания видео из социальных сетей.

📥 ПОДДЕРЖИВАЕМЫЕ ПЛАТФОРМЫ:

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 И другие поддерживаемые платформы.

🎬 ВОЗМОЖНОСТИ:

✅ Скачивание видео в MP4.
✅ Доступные варианты качества.
✅ Скачивание по ссылке.

👥 ФУНКЦИИ ДЛЯ ГРУПП:

🧹 Автоматическое удаление сообщений о входе и выходе участников.

🚫 Удаление рекламы и нежелательных ссылок.

⚙️ Предоставьте боту права администратора и разрешение на удаление сообщений.

➕ ДОБАВИТЬ БОТА В ГРУППУ!

❤️ Спасибо за использование нашего бота!""",
        "link": "📩 Отправьте ссылку на видео.",
        "working": "⏳ Загружаем видео...",
        "success": f"✅ Видео загружено!\n\nСпасибо за использование @{BOT_USERNAME}! 🔥\n\n👥 Удаление сообщений о входе и выходе.\n🚫 Удаление рекламы.",
        "error": "❌ Не удалось скачать видео. Попробуйте другую ссылку.",
        "youtube_error": "❗ Не удалось скачать YouTube-видео. Возможны ограничения YouTube.",
        "button": "🎬 Скачать видео",
        "group": "➕ Добавить в группу",
        "selected": "✅ Язык изменён.",
        "accepted": "✅ Ссылка принята:"
    },

    "en": {
        "choose": "🌐 Choose your language:",
        "welcome": """👋 Hello!

🚀 Welcome to SAVE VIDEO!

I am a social media video downloader bot.

📥 SUPPORTED PLATFORMS:

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 Other supported platforms.

🎬 FEATURES:

✅ MP4 video downloads.
✅ Available quality options.
✅ Download using a link.

👥 GROUP FEATURES:

🧹 Automatically deletes join and leave notifications.

🚫 Helps remove advertisements and unwanted links.

⚙️ Give the bot administrator rights and permission to delete messages.

➕ ADD BOT TO GROUP!

❤️ Thank you for using our bot!""",
        "link": "📩 Please send a video link.",
        "working": "⏳ Downloading video...",
        "success": f"✅ Download complete!\n\nThank you for using @{BOT_USERNAME}! 🔥\n\n👥 Join and leave notifications are removed.\n🚫 Helps remove advertisements.",
        "error": "❌ Download failed. Try another link.",
        "youtube_error": "❗ Could not download YouTube video. Platform restrictions may apply.",
        "button": "🎬 Download video",
        "group": "➕ Add to group",
        "selected": "✅ Language changed.",
        "accepted": "✅ Link accepted:"
    },

    "ar": {
        "choose": "🌐 اختر اللغة:",
        "welcome": """👋 مرحباً!

🚀 أهلاً بك في SAVE VIDEO!

أنا بوت لتحميل الفيديوهات من مواقع التواصل الاجتماعي.

📥 المنصات المدعومة:

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 ومنصات أخرى مدعومة.

🎬 المميزات:

✅ تحميل الفيديو بصيغة MP4.
✅ خيارات الجودة المتاحة.
✅ التحميل باستخدام الرابط.

👥 مميزات المجموعات:

🧹 حذف رسائل دخول وخروج الأعضاء تلقائياً.

🚫 المساعدة في حذف الإعلانات والروابط غير المرغوب فيها.

⚙️ امنح البوت صلاحيات المشرف وإذن حذف الرسائل.

➕ أضف البوت إلى المجموعة!

❤️ شكراً لاستخدامك البوت!""",
        "link": "📩 أرسل رابط الفيديو.",
        "working": "⏳ جارٍ تحميل الفيديو...",
        "success": f"✅ اكتمل التحميل!\n\nشكراً لاستخدام @{BOT_USERNAME}! 🔥",
        "error": "❌ تعذر تحميل الفيديو. جرب رابطاً آخر.",
        "youtube_error": "❗ تعذر تحميل فيديو YouTube. قد تكون هناك قيود.",
        "button": "🎬 تحميل الفيديو",
        "group": "➕ أضف إلى المجموعة",
        "selected": "✅ تم تغيير اللغة.",
        "accepted": "✅ تم قبول الرابط:"
    }
}

# =============== DATABASE ===============

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with db_lock:
        conn = db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_type TEXT
            )
        """)
        conn.commit()
        conn.close()


def save_user(chat_id):
    with db_lock:
        conn = db()
        conn.execute(
            "INSERT OR IGNORE INTO users(chat_id) VALUES(?)",
            (chat_id,)
        )
        conn.commit()
        conn.close()


def save_chat(chat_id, chat_type):
    with db_lock:
        conn = db()
        conn.execute(
            "INSERT OR REPLACE INTO chats VALUES(?, ?)",
            (chat_id, chat_type)
        )
        conn.commit()
        conn.close()


def get_lang(chat_id):
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT lang FROM users WHERE chat_id=?",
            (chat_id,)
        ).fetchone()
        conn.close()

    return row[0] if row else "uz"


def set_lang(chat_id, lang):
    with db_lock:
        conn = db()
        conn.execute(
            "UPDATE users SET lang=? WHERE chat_id=?",
            (lang, chat_id)
        )
        conn.commit()
        conn.close()


# =============== KEYBOARD ===============

def language_keyboard():
    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "🇺🇿 O‘zbekcha", callback_data="lang_uz"
        ),
        types.InlineKeyboardButton(
            "🇷🇺 Русский", callback_data="lang_ru"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "🇬🇧 English", callback_data="lang_en"
        ),
        types.InlineKeyboardButton(
            "🇸🇦 العربية", callback_data="lang_ar"
        )
    )

    return markup


def main_keyboard(lang):
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            TEXTS[lang]["group"],
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    )

    return markup


# =============== START ===============

@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type != "private":
        return

    save_user(message.chat.id)

    bot.send_message(
        message.chat.id,
        TEXTS[get_lang(message.chat.id)]["choose"],
        reply_markup=language_keyboard()
    )


@bot.message_handler(commands=["lang"])
def change_language(message):
    bot.send_message(
        message.chat.id,
        "🌐 Tilni tanlang / Choose language:",
        reply_markup=language_keyboard()
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("lang_")
)
def language_callback(call):
    lang = call.data.split("_", 1)[1]

    if lang not in TEXTS:
        return

    save_user(call.message.chat.id)
    set_lang(call.message.chat.id, lang)

    bot.answer_callback_query(
        call.id,
        TEXTS[lang]["selected"]
    )

    bot.send_message(
        call.message.chat.id,
        TEXTS[lang]["welcome"],
        reply_markup=main_keyboard(lang)
    )


# =============== VIDEO YUKLASH ===============

def extract_video(url, folder):
    output = os.path.join(
        folder,
        "%(title).70s-%(id)s.%(ext)s"
    )

    options = {
        "outtmpl": output,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "quiet": True,
        "no_warnings": False,
        "cachedir": False,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        filepath = None

        for item in info.get("requested_downloads") or []:
            candidate = item.get("filepath")
            if candidate and os.path.isfile(candidate):
                filepath = candidate
                break

        if not filepath:
            filepath = ydl.prepare_filename(info)

        if not os.path.isfile(filepath):
            base = os.path.splitext(
                os.path.basename(filepath)
            )[0]

            candidates = [
                os.path.join(folder, name)
                for name in os.listdir(folder)
                if name.startswith(base)
            ]

            if candidates:
                filepath = candidates[0]

        if not os.path.isfile(filepath):
            raise FileNotFoundError("Video fayli topilmadi")

        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            raise ValueError("Video 49 MB limitdan katta")

        return filepath


def download_and_send(chat_id, url, status_id):
    folder = tempfile.mkdtemp(prefix="video_")

    try:
        with download_lock:
            filepath = extract_video(url, folder)
            lang = get_lang(chat_id)

            with open(filepath, "rb") as video:
                bot.send_video(
                    chat_id,
                    video,
                    supports_streaming=True,
                    caption=f"🎬 @{BOT_USERNAME}"
                )

            bot.send_message(
                chat_id,
                TEXTS[lang]["success"],
                reply_markup=main_keyboard(lang)
            )

        try:
            bot.delete_message(chat_id, status_id)
        except Exception:
            pass

    except Exception as error:
        logging.exception("Download error: %s", error)

        lang = get_lang(chat_id)
        text = TEXTS[lang]["error"]

        if "youtube.com" in url or "youtu.be" in url:
            text = TEXTS[lang]["youtube_error"]

        try:
            bot.edit_message_text(
                text,
                chat_id,
                status_id
            )
        except Exception:
            bot.send_message(chat_id, text)

    finally:
        shutil.rmtree(folder, ignore_errors=True)


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("download_")
)
def download_callback(call):
    key = call.data.replace("download_", "", 1)
    url = pending_downloads.pop(key, None)

    if not url:
        bot.answer_callback_query(
            call.id,
            "Havola muddati tugagan."
        )
        return

    bot.answer_callback_query(call.id)

    lang = get_lang(call.message.chat.id)

    status = bot.send_message(
        call.message.chat.id,
        TEXTS[lang]["working"]
    )

    threading.Thread(
        target=download_and_send,
        args=(
            call.message.chat.id,
            url,
            status.message_id
        ),
        daemon=True
    ).start()


# =============== HAVOLALAR VA ADMIN XABarlari ===============

URL_RE = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE
)


@bot.message_handler(
    content_types=["text"],
    func=lambda m: m.chat.type == "private" and not m.text.startswith("/")
)
def private_text(message):
    save_user(message.chat.id)

    # Agar admin xabar yuborish rejimida bo'lsa
    if message.chat.id in broadcast_waiting:
        broadcast_waiting.discard(message.chat.id)
        broadcast(message)
        return

    lang = get_lang(message.chat.id)
    match = URL_RE.search(message.text or "")

    # Agar o'zingiz (Admin) yozgan bo'lsangiz va havola tashlamagan bo'lsangiz:
    if message.from_user.id == ADMIN_ID and not match:
        bot.reply_to(message, "Buyruq yoki so'zingiz qabul qilindi! 😎")
        return

    if not match:
        bot.reply_to(
            message,
            TEXTS[lang]["link"]
        )
        return

    url = match.group(0).rstrip(".,)")

    key = uuid.uuid4().hex[:12]
    pending_downloads[key] = url

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            TEXTS[lang]["button"],
            callback_data=f"download_{key}"
        )
    )

    bot.reply_to(
        message,
        TEXTS[lang]["accepted"],
        reply_markup=markup
    )


# =============== ADMIN ===============

def is_admin(message):
    return (
        message.from_user
        and message.from_user.id == ADMIN_ID
    )


@bot.message_handler(commands=["stats"])
def stats(message):
    if not is_admin(message):
        return

    with db_lock:
        conn = db()

        users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        groups = conn.execute(
            "SELECT COUNT(*) FROM chats"
        ).fetchone()[0]

        conn.close()

    bot.reply_to(
        message,
        f"📊 BOT STATISTIKASI\n\n"
        f"👤 Foydalanuvchilar: {users}\n"
        f"👥 Guruhlar: {groups}"
    )


@bot.message_handler(commands=["send"])
def send_command(message):
    if not is_admin(message):
        return

    broadcast_waiting.add(message.chat.id)

    bot.reply_to(
        message,
        "📢 Yuboriladigan matn yoki rasmni jo‘nating.\n"
        "Bekor qilish: /cancel"
    )


@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if message.chat.id in broadcast_waiting:
        broadcast_waiting.discard(message.chat.id)
        bot.reply_to(message, "❌ Bekor qilindi.")


def broadcast(message):
    with db_lock:
        conn = db()

        targets = [
            row[0] for row in conn.execute(
                "SELECT chat_id FROM users"
            ).fetchall()
        ]

        targets += [
            row[0] for row in conn.execute(
                "SELECT chat_id FROM chats"
            ).fetchall()
        ]

        conn.close()

    sent = 0

    for chat_id in set(targets):
        try:
            bot.copy_message(
                chat_id,
                message.chat.id,
                message.message_id
            )
            sent += 1
            time.sleep(0.05)
        except Exception:
            logging.warning(
                "Broadcast failed: %s",
                chat_id
            )

    bot.send_message(
        message.chat.id,
        f"✅ Yuborildi: {sent} ta chat"
    )


@bot.message_handler(
    content_types=[
        "photo", "video", "document",
        "animation", "audio", "voice"
    ],
    func=lambda m: (
        m.chat.type == "private"
        and m.chat.id in broadcast_waiting
    )
)
def broadcast_media(message):
    broadcast_waiting.discard(message.chat.id)
    broadcast(message)


# =============== GURUH MODERATORI ===============

@bot.message_handler(
    content_types=["new_chat_members"]
)
def new_members(message):
    save_chat(message.chat.id, message.chat.type)

    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception as error:
        logging.warning("Join delete: %s", error)


@bot.message_handler(
    content_types=["left_chat_member"]
)
def left_member(message):
    save_chat(message.chat.id, message.chat.type)

    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception as error:
        logging.warning("Leave delete: %s", error)


def is_advertisement(message):
    text = message.text or message.caption or ""
    return bool(URL_RE.search(text))


@bot.message_handler(
    content_types=[
        "text", "photo", "video",
        "document", "animation"
    ],
    func=lambda m: m.chat.type in [
        "group", "supergroup"
    ]
)
def group_moderation(message):
    save_chat(message.chat.id, message.chat.type)

    if message.from_user:
        if message.from_user.id == ADMIN_ID:
            return

    if is_advertisement(message):
        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )
        except Exception as error:
            logging.warning(
                "Advertisement delete: %s",
                error
            )


# =============== SERVER ===============

@app.route("/")
def home():
    return "SAVE VIDEO bot ishlayapti!"


@app.route("/health")
def health():
    return "OK"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )


# =============== ISHGA TUSHIRISH ===============

if __name__ == "__main__":
    init_db()

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    logging.info("SAVE VIDEO bot ishga tushdi!")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30
    )
