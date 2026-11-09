
import os
import re
import glob
import sqlite3
import tempfile
import threading
import logging

from flask import Flask
import telebot
from telebot import types
import yt_dlp

# =============== SOZLAMALAR ===============

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8019481444
BOT_USERNAME = "SaveToVid_bot"

PORT = int(os.getenv("PORT", "10000"))
MAX_FILE_SIZE = 500 * 1024 * 1024
DB_PATH = os.getenv("DB_PATH", "bot.db")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN sozlanmagan!")

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============== FLASK ===============

@app.route("/")
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# =============== DATABASE ===============

def db():
    return sqlite3.connect(DB_PATH, timeout=30)

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uz'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_type TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                downloads INTEGER DEFAULT 0
            )
        """)
        conn.execute(
            "INSERT OR IGNORE INTO stats VALUES (1, 0)"
        )

def register_user(message):
    if message.from_user:
        with db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                (message.from_user.id,)
            )

    if message.chat.type in ("group", "supergroup", "channel"):
        with db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO chats VALUES (?, ?)",
                (message.chat.id, message.chat.type)
            )

def get_lang(user_id):
    with db() as conn:
        row = conn.execute(
            "SELECT language FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()
    return row[0] if row else "uz"

def set_lang(user_id, language):
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        conn.execute(
            "UPDATE users SET language=? WHERE user_id=?",
            (language, user_id)
        )

def add_download():
    with db() as conn:
        conn.execute(
            "UPDATE stats SET downloads=downloads+1 WHERE id=1"
        )

init_db()

# =============== TILLAR ===============

LANG_DATA = {
    "uz": {
        "welcome": (
            "🔥 **Assalomu alaykum!**\n"
            f"@{BOT_USERNAME} botiga xush kelibsiz!\n\n"
            "Quyidagi platformalardan video yuklashga urinib ko'rishingiz mumkin:\n"
            "• Instagram\n• TikTok\n• YouTube\n"
            "• Likee\n• Pinterest\n• Threads\n"
            "• Snapchat va boshqa qo'llab-quvvatlanadigan saytlar\n\n"
            "🚀 Yuklamoqchi bo'lgan videongiz havolasini yuboring!\n"
            "😎 Bot guruhlarda ham ishlay oladi!"
        ),
        "selected": "🇺🇿 Til O'zbekchaga o'zgartirildi!",
        "loading": "⏳ Video yuklab olinmoqda...",
        "success": (
            "✅ **Yuklab olindi!**\n\n"
            f"Yuborgan linkingiz uchun @{BOT_USERNAME} nomidan sizga rahmat! 🚀\n\n"
            "✨ Guruhingizni tartibli saqlang! "
            "Bot guruhdagi kirdi-chiqdi xabarlarini o'chirishga yordam beradi."
        ),
        "error": "❌ Videoni yuklab bo'lmadi. Havolani tekshirib qayta urinib ko'ring.",
        "large": "❌ Fayl hajmi Telegram cheklovidan katta.",
        "send_link": "Iltimos, to'g'ri video havolasini yuboring."
    },
    "uz_kr": {
        "welcome": (
            "🔥 **Ассалому алайкум!**\n"
            f"@{BOT_USERNAME} ботига хуш келибсиз!\n\n"
            "Instagram, TikTok, YouTube, Likee, Pinterest, "
            "Threads ва бошқа платформалардан видео юклашга уриниб кўринг.\n\n"
            "🚀 Видео ҳаволасини юборинг!"
        ),
        "selected": "🇺🇿 Тил ўзбекчага ўзгартирилди!",
        "loading": "⏳ Видео юкланмоқда...",
        "success": f"✅ **Юклаб олинди!**\n\n@{BOT_USERNAME} номидан раҳмат! 🚀",
        "error": "❌ Видеони юклаб бўлмади. Ҳаволани текширинг.",
        "large": "❌ Файл ҳажми жуда катта.",
        "send_link": "Илтимос, видео ҳаволасини юборинг."
    },
    "ru": {
        "welcome": (
            "🔥 **Здравствуйте!**\n"
            f"Добро пожаловать в @{BOT_USERNAME}!\n\n"
            "Поддерживаемые платформы: Instagram, TikTok, YouTube, "
            "Likee, Pinterest, Threads и другие.\n\n"
            "🚀 Отправьте ссылку на видео!"
        ),
        "selected": "🇷🇺 Язык изменён на русский!",
        "loading": "⏳ Видео загружается...",
        "success": "✅ **Видео скачано!**\n\nСпасибо за использование бота! 🚀",
        "error": "❌ Не удалось скачать видео. Проверьте ссылку.",
        "large": "❌ Размер файла слишком большой.",
        "send_link": "Отправьте правильную ссылку на видео."
    },
    "en": {
        "welcome": (
            "🔥 **Hello!**\n"
            f"Welcome to @{BOT_USERNAME}!\n\n"
            "Supported platforms include Instagram, TikTok, YouTube, "
            "Likee, Pinterest, Threads and others.\n\n"
            "🚀 Send a video link!"
        ),
        "selected": "🇬🇧 Language changed to English!",
        "loading": "⏳ Downloading video...",
        "success": "✅ **Downloaded successfully!**\n\nThank you for using our bot! 🚀",
        "error": "❌ Could not download the video. Check the link.",
        "large": "❌ File is too large.",
        "send_link": "Please send a valid video link."
    },
    "ar": {
        "welcome": (
            "🔥 **مرحباً بك!**\n"
            f"أهلاً بك في @{BOT_USERNAME}!\n\n"
            "المنصات المدعومة تشمل Instagram وTikTok وYouTube وغيرها.\n\n"
            "🚀 أرسل رابط الفيديو!"
        ),
        "selected": "🇸🇦 تم تغيير اللغة إلى العربية!",
        "loading": "⏳ جارٍ تنزيل الفيديو...",
        "success": "✅ **تم التنزيل بنجاح!**\n\nشكراً لاستخدام البوت! 🚀",
        "error": "❌ تعذر تنزيل الفيديو. تحقق من الرابط.",
        "large": "❌ حجم الملف كبير جداً.",
        "send_link": "أرسل رابط فيديو صحيحاً."
    }
}

# =============== TIL TUGMALARI ===============

def get_language_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇺🇿 Ўзбекча", callback_data="lang_uz_kr"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    return markup

def group_keyboard(lang):
    names = {
        "uz": "➕ Guruhga qo'shish",
        "uz_kr": "➕ Гуруҳга қўшиш",
        "ru": "➕ Добавить в группу",
        "en": "➕ Add to group",
        "ar": "➕ أضف إلى المجموعة"
    }

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            names[lang],
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    )
    return markup

# =============== START ===============

@bot.message_handler(commands=["start"])
def start(message):
    register_user(message)

    intro = (
        "O'zingizga qulay tilni tanlang 🇺🇿\n"
        "Ўзингизга қулай тилни танланг 🇺🇿\n"
        "Выберите удобный язык 🇷🇺\n"
        "Choose your language 🇬🇧\n"
        "اختر لغتك 🇸🇦"
    )

    bot.send_message(
        message.chat.id,
        intro,
        reply_markup=get_language_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def language_callback(call):
    lang = call.data.replace("lang_", "", 1)

    if lang not in LANG_DATA:
        bot.answer_callback_query(call.id, "Noto'g'ri til!")
        return

    set_lang(call.from_user.id, lang)
    bot.answer_callback_query(call.id, "Til saqlandi!")

    bot.send_message(
        call.message.chat.id,
        LANG_DATA[lang]["selected"] + "\n\n" + LANG_DATA[lang]["welcome"],
        parse_mode="Markdown",
        reply_markup=group_keyboard(lang)
    )

# =============== STATISTIKA ===============

@bot.message_handler(commands=["stats"])
def stats(message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu buyruq faqat admin uchun!")
        return

    with db() as conn:
        users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        chats = conn.execute(
            "SELECT COUNT(*) FROM chats"
        ).fetchone()[0]

        downloads = conn.execute(
            "SELECT downloads FROM stats WHERE id=1"
        ).fetchone()[0]

    bot.reply_to(
        message,
        f"📊 **BOT STATISTIKASI**\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"👥 Guruh va kanallar: {chats}\n"
        f"📥 Yuklangan videolar: {downloads}",
        parse_mode="Markdown"
    )

# =============== ADMIN XABAR TARQATISH ===============

@bot.message_handler(commands=["send"], content_types=["text", "photo"])
def broadcast(message):
    if not message.from_user or message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu buyruq faqat admin uchun!")
        return

    if message.content_type == "photo":
        caption = re.sub(
            r"^/send(?:@\w+)?\s*",
            "",
            message.caption or ""
        ).strip()
        photo_id = message.photo[-1].file_id
    else:
        parts = message.text.split(maxsplit=1)
        caption = parts[1] if len(parts) > 1 else ""
        photo_id = None

    if not caption and not photo_id:
        bot.reply_to(
            message,
            "Tarqatish uchun matn yoki rasm yuboring.\n"
            "Masalan: /send Assalomu alaykum!"
        )
        return

    with db() as conn:
        users = conn.execute("SELECT user_id FROM users").fetchall()
        chats = conn.execute("SELECT chat_id FROM chats").fetchall()

    targets = set(row[0] for row in users + chats)
    success = 0
    failed = 0

    for target in targets:
        try:
            if photo_id:
                bot.send_photo(target, photo_id, caption=caption)
            else:
                bot.send_message(target, caption)
            success += 1
        except Exception as e:
            failed += 1
            logger.warning("Xabar yuborilmadi: %s", e)

    bot.reply_to(
        message,
        f"✅ Yuborildi: {success}\n❌ Yuborilmadi: {failed}"
    )

# =============== VIDEO YUKLASH ===============

URL_PATTERN = re.compile(r"https?://[^\s]+")

def download_video(url, folder):
    options = {
        "outtmpl": os.path.join(folder, "%(id)s.%(ext)s"),
        "format": "best[height<=720]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 2
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        if info.get("_type") == "playlist":
            raise ValueError("Playlist qo'llab-quvvatlanmaydi")

        files = glob.glob(os.path.join(folder, "*"))

        if not files:
            raise FileNotFoundError("Yuklangan fayl topilmadi")

        filepath = max(files, key=os.path.getsize)

        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            raise OverflowError("FILE_TOO_LARGE")

        return filepath

@bot.message_handler(
    content_types=["text"],
    func=lambda message: not (message.text or "").startswith("/")
)
def handle_link(message):
    register_user(message)

    if not message.from_user:
        return

    urls = URL_PATTERN.findall(message.text.strip())
    lang = get_lang(message.from_user.id)

    if not urls:
        bot.reply_to(message, LANG_DATA[lang]["send_link"])
        return

    url = urls[0]

    status = bot.reply_to(
        message,
        LANG_DATA[lang]["loading"]
    )

    try:
        with tempfile.TemporaryDirectory() as folder:
            filepath = download_video(url, folder)

            with open(filepath, "rb") as video:
                try:
                    bot.send_video(
                        message.chat.id,
                        video,
                        caption=LANG_DATA[lang]["success"],
                        parse_mode="Markdown",
                        reply_markup=group_keyboard(lang),
                        timeout=120
                    )
                except Exception:
                    video.seek(0)
                    bot.send_document(
                        message.chat.id,
                        video,
                        caption=LANG_DATA[lang]["success"],
                        parse_mode="Markdown",
                        reply_markup=group_keyboard(lang),
                        timeout=120
                    )

            add_download()

        bot.delete_message(message.chat.id, status.message_id)

    except OverflowError:
        bot.edit_message_text(
            LANG_DATA[lang]["large"],
            message.chat.id,
            status.message_id
        )

    except Exception as e:
        logger.exception("Yuklash xatosi: %s", e)
        bot.edit_message_text(
            LANG_DATA[lang]["error"],
            message.chat.id,
            status.message_id
        )

# =============== GURUH TOZALASH ===============

@bot.message_handler(content_types=["new_chat_members"])
def delete_join(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

@bot.message_handler(content_types=["left_chat_member"])
def delete_leave(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

# =============== ISHGA TUSHIRISH ===============

if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("SaveToVid_bot ishga tushdi!")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
