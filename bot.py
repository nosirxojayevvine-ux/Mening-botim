
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
ADMIN_USERNAME = "@nosirxojayev"

# TO'G'RILANGAN BOT USERNAME
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


# =============== DATABASE ===============

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with db_lock:
        conn = db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz'
            )
        """)

        cur.execute("""
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
            "INSERT OR REPLACE INTO chats(chat_id, chat_type) VALUES(?, ?)",
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


# =============== TILLAR ===============

TEXTS = {
    "uz": {
        "choose": "🌐 Tilni tanlang:",

        "welcome": """👋 Assalomu alaykum!

🚀 SAVE VIDEO botiga xush kelibsiz!

Men sizga ijtimoiy tarmoqlardagi video va media fayllarni tez va qulay yuklab olishda yordam beraman.

📥 VIDEO YUKLAB OLISH

Quyidagi platformalardan video havolalarini yuboring:

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 Va boshqa qo‘llab-quvvatlanadigan platformalar.

🎬 YUKLAB OLISH IMKONIYATLARI

✅ Videolarni MP4 formatida yuklab olish.
✅ Mavjud sifat variantlarini tanlash.
✅ Havola orqali yuklab olish.
✅ Sodda va qulay foydalanish.

👥 GURUHLAR UCHUN MAXSUS IMKONIYATLAR

Botni guruhingizga qo‘shing:

🧹 Kirdi-chiqdi xabarlarini avtomatik o‘chirish — guruhga a'zo qo‘shilganda yoki a'zo chiqib ketganda paydo bo‘ladigan xabarlarni o‘chiradi.

🚫 Reklama va keraksiz xabarlarni o‘chirishga yordam beradi.

🔒 Guruhingizni tartibli va ozoda saqlang!

⚙️ Ushbu imkoniyatlar ishlashi uchun botga administrator huquqi va xabarlarni o‘chirish ruxsatini bering.

➕ BOTNI GURUHGA QO‘SHING

❤️ Xizmatimizdan foydalanganingiz uchun rahmat!

📩 Video havolasini yuboring va yuklab olishni boshlang!""",

        "link": "📩 Iltimos, video havolasini yuboring.",
        "working": "⏳ Video/MP4 yuklab olinmoqda...",
        "success": f"""✅ Yuklab olindi!

Yuborgan linkingiz uchun @{BOT_USERNAME} nomidan sizga rahmat! 🔥

✨ Botning qo‘shimcha funksiyalari:

👥 Guruhlarda kirdi-chiqdi xabarlarini avtomatik o‘chiradi.
🚫 Reklama va keraksiz xabarlarni o‘chirishga yordam beradi.

❤️ Biz bilan qoling!""",
        "error": "❌ Videoni yuklab bo‘lmadi. Boshqa havolani yuborib ko‘ring.",
        "youtube_error": "❗ YouTube videosini yuklab bo‘lmadi. Havola yoki YouTube cheklovlari sabab bo‘lishi mumkin.",
        "button": "🎬 Videoni yuklab olish",
        "group": "➕ Guruhga qo‘shish",
        "selected": "✅ Til o‘zgartirildi.",
        "accepted": "✅ Havola qabul qilindi:"
    },

    "ru": {
        "choose": "🌐 Выберите язык:",

        "welcome": """👋 Здравствуйте!

🚀 Добро пожаловать в SAVE VIDEO!

Я помогу вам быстро и удобно скачивать видео из социальных сетей.

📥 СКАЧИВАНИЕ ВИДЕО

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 И другие поддерживаемые платформы.

🎬 ВОЗМОЖНОСТИ

✅ Скачивание видео в MP4.
✅ Выбор доступного качества.
✅ Скачивание по ссылке.
✅ Простой интерфейс.

👥 ВОЗМОЖНОСТИ ДЛЯ ГРУПП

🧹 Автоматическое удаление сообщений о входе и выходе участников.

🚫 Удаление рекламы и нежелательных сообщений.

🔒 Поддерживайте порядок в своей группе!

⚙️ Для работы функций предоставьте боту права администратора и разрешение на удаление сообщений.

➕ ДОБАВИТЬ БОТА В ГРУППУ

❤️ Спасибо за использование нашего бота!

📩 Отправьте ссылку на видео!""",

        "link": "📩 Отправьте ссылку на видео.",
        "working": "⏳ Загружаем видео...",
        "success": f"✅ Видео загружено!\n\nСпасибо за использование @{BOT_USERNAME}! 🔥\n\n👥 Бот удаляет сообщения о входе и выходе участников.\n🚫 Помогает удалять рекламу.",
        "error": "❌ Не удалось скачать видео. Попробуйте другую ссылку.",
        "youtube_error": "❗ Не удалось скачать YouTube-видео. Возможны ограничения платформы.",
        "button": "🎬 Скачать видео",
        "group": "➕ Добавить в группу",
        "selected": "✅ Язык изменён.",
        "accepted": "✅ Ссылка принята:"
    },

    "en": {
        "choose": "🌐 Choose your language:",

        "welcome": """👋 Hello!

🚀 Welcome to SAVE VIDEO!

I help you download videos from social networks quickly and easily.

📥 VIDEO DOWNLOADING

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 And other supported platforms.

🎬 FEATURES

✅ Download videos in MP4.
✅ Choose available quality.
✅ Download using a link.
✅ Simple interface.

👥 GROUP FEATURES

🧹 Automatically delete join and leave notifications.

🚫 Delete advertisements and unwanted messages.

🔒 Keep your group clean and organized!

⚙️ Give the bot administrator rights and permission to delete messages.

➕ ADD BOT TO GROUP

❤️ Thank you for using our service!

📩 Send a video link to get started!""",

        "link": "📩 Please send a video link.",
        "working": "⏳ Downloading video...",
        "success": f"✅ Download complete!\n\nThank you for using @{BOT_USERNAME}! 🔥\n\n👥 Automatically deletes join and leave notifications.\n🚫 Helps remove advertisements.",
        "error": "❌ Download failed. Please try another link.",
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

أساعدك على تحميل الفيديوهات من مواقع التواصل الاجتماعي بسهولة.

📥 تحميل الفيديوهات

📸 Instagram
▶️ YouTube
🎵 TikTok
💜 Likee
🌐 ومنصات أخرى مدعومة.

🎬 المميزات

✅ تحميل الفيديو بصيغة MP4.
✅ اختيار الجودة المتاحة.
✅ التحميل باستخدام الرابط.
✅ واجهة سهلة.

👥 مميزات المجموعات

🧹 حذف رسائل دخول وخروج الأعضاء تلقائياً.

🚫 حذف الإعلانات والرسائل غير المرغوب فيها.

🔒 حافظ على مجموعتك منظمة!

⚙️ امنح البوت صلاحيات المشرف وإذن حذف الرسائل.

➕ أضف البوت إلى المجموعة

❤️ شكراً لاستخدامك خدمتنا!

📩 أرسل رابط الفيديو للبدء!""",

        "link": "📩 أرسل رابط الفيديو.",
        "working": "⏳ جارٍ تحميل الفيديو...",
        "success": f"✅ اكتمل التحميل!\n\nشكراً لاستخدام @{BOT_USERNAME}! 🔥\n\n👥 يحذف رسائل دخول وخروج الأعضاء.\n🚫 يساعد في حذف الإعلانات.",
        "error": "❌ تعذر تحميل الفيديو. جرب رابطاً آخر.",
        "youtube_error": "❗ تعذر تحميل فيديو YouTube. قد تكون هناك قيود على المنصة.",
        "button": "🎬 تحميل الفيديو",
        "group": "➕ أضف إلى المجموعة",
        "selected": "✅ تم تغيير اللغة.",
        "accepted": "✅ تم قبول الرابط:"
    }
}


# =============== MENYU ===============

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

    lang = get_lang(message.chat.id)

    bot.send_message(
        message.chat.id,
        TEXTS[lang]["choose"],
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


# =============== YUKLAB OLISH ===============

def extract_video(url, folder):
    output = os.path.join(
        folder,
        "%(title).80s-%(id)s.%(ext)s"
    )

    options = {
        "outtmpl": output,
        "format": "best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "quiet": True,
        "no_warnings": True,
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
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.startswith(base)
            ]

            if candidates:
                filepath = candidates[0]

        if not os.path.isfile(filepath):
            raise FileNotFoundError("Video fayli topilmadi")

        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            raise ValueError("Video hajmi limitdan katta")

        return filepath


def download_and_send(chat_id, url, status_message_id):
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
                TEXTS[lang]["success"]
            )

        try:
            bot.delete_message(
                chat_id,
                status_message_id
            )
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
                status_message_id
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
    item = pending_downloads.pop(key, None)

    if not item:
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
            item,
            status.message_id
        ),
        daemon=True
    ).start()


# =============== HAVOLALAR ===============

URL_RE = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE
)


@bot.message_handler(
    content_types=["text"],
    func=lambda m: m.chat.type == "private"
)
def private_text(message):
    save_user(message.chat.id)

    if message.chat.id in broadcast_waiting:
        broadcast_waiting.discard(message.chat.id)
        broadcast(message)
        return

    lang = get_lang(message.chat.id)

    match = URL_RE.search(message.text or "")

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


# =============== ADMIN BUYRUQLARI ===============

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
        f"""📊 BOT STATISTIKASI

👤 Foydalanuvchilar: {users}
👥 Guruhlar: {groups}"""
    )


@bot.message_handler(commands=["send"])
def send_command(message):
    if not is_admin(message):
        return

    broadcast_waiting.add(message.chat.id)

    bot.reply_to(
        message,
        "📢 Yuboriladigan matn, rasm yoki xabarni jo‘nating.\n\nBekor qilish: /cancel"
    )


@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if message.chat.id in broadcast_waiting:
        broadcast_waiting.discard(message.chat.id)

        bot.reply_to(
            message,
            "❌ Yuborish bekor qilindi."
        )


def broadcast(message):
    with db_lock:
        conn = db()

        targets = [
            x[0] for x in conn.execute(
                "SELECT chat_id FROM users"
            ).fetchall()
        ]

        targets += [
            x[0] for x in conn.execute(
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

        except Exception as error:
            logging.warning(
                "Broadcast failed for %s: %s",
                chat_id,
                error
            )

    bot.send_message(
        message.chat.id,
        f"✅ Yuborildi: {sent} ta chat"
    )


@bot.message_handler(
    content_types=[
        "photo",
        "video",
        "document",
        "animation",
        "audio",
        "voice"
    ],
    func=lambda m: (
        m.chat.type == "private"
        and m.chat.id in broadcast_waiting
    )
)
def broadcast_media(message):
    broadcast_waiting.discard(message.chat.id)
    broadcast(message)


# =============== GURUH FUNKSIYALARI ===============

@bot.message_handler(
    content_types=["new_chat_members"]
)
def new_members(message):
    save_chat(
        message.chat.id,
        message.chat.type
    )

    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception as error:
        logging.warning(
            "Join notification delete failed: %s",
            error
        )


@bot.message_handler(
    content_types=["left_chat_member"]
)
def left_member(message):
    save_chat(
        message.chat.id,
        message.chat.type
    )

    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception as error:
        logging.warning(
            "Leave notification delete failed: %s",
            error
        )


def is_advertisement(message):
    text = message.text or message.caption or ""

    if URL_RE.search(text):
        return True

    return False


@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "animation"
    ],
    func=lambda m: m.chat.type in [
        "group",
        "supergroup"
    ]
)
def group_moderation(message):
    save_chat(
        message.chat.id,
        message.chat.type
    )

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
                "Advertisement delete failed: %s",
                error
            )


# =============== SERVER ===============

@app.route("/")
def home():
    return "Bot ishlayapti!"


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

    logging.info("Bot ishga tushdi!")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30
    )
