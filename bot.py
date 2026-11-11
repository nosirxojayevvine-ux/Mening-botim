
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
        "welcome": "Assalomu alaykum! 👋\n\nMen ijtimoiy tarmoqlardan video yuklab beruvchi botman.\n\nInstagram, YouTube, TikTok va boshqa havolalarni yuboring.",
        "choose": "Tilni tanlang:",
        "link": "Video havolasini yuboring.",
        "working": "⏳ Video/MP4 yuklab olinmoqda...",
        "success": "✅ Yuklab olindi!\n\nYuborgan linkingiz uchun @SaveToVid_bot nomidan sizga rahmat! 🔥\n\n✨ Botning qo‘shimcha funksiyasi:\n👥 Guruhlarda kirish-chiqish xabarlarini avtomatik o‘chiradi.\n🚫 Reklama xabarlarini ham o‘chirishi mumkin.",
        "error": "❌ Videoni yuklab bo‘lmadi. Boshqa havolani yuborib ko‘ring.",
        "youtube_error": "❗ Uzr, YouTube videosini yuklab bera olmadik. YouTube xavfsizlik cheklovlari sababli xatolik yuz bergan bo‘lishi mumkin.",
        "button": "🎬 Videoni yuklab olish",
        "group": "➕ Guruhga qo‘shish",
        "selected": "Til o‘zgartirildi."
    },
    "ru": {
        "welcome": "Здравствуйте! 👋\n\nЯ бот для скачивания видео из социальных сетей.\nОтправьте ссылку на видео.",
        "choose": "Выберите язык:",
        "link": "Отправьте ссылку на видео.",
        "working": "⏳ Видео загружается...",
        "success": "✅ Видео загружено! Спасибо за использование @SaveToVid_bot!",
        "error": "❌ Не удалось скачать видео. Попробуйте другую ссылку.",
        "youtube_error": "Не удалось скачать YouTube-видео. Возможно, действуют ограничения YouTube.",
        "button": "🎬 Скачать видео",
        "group": "➕ Добавить в группу",
        "selected": "Язык изменён."
    },
    "en": {
        "welcome": "Hello! 👋\n\nI am a video downloader bot. Send a video link.",
        "choose": "Choose your language:",
        "link": "Please send a video link.",
        "working": "⏳ Downloading video...",
        "success": "✅ Download complete! Thank you for using @SaveToVid_bot!",
        "error": "❌ Download failed. Try another link.",
        "youtube_error": "Could not download YouTube video. YouTube restrictions may be responsible.",
        "button": "🎬 Download video",
        "group": "➕ Add to group",
        "selected": "Language changed."
    },
    "ar": {
        "welcome": "مرحباً! 👋\n\nأنا بوت لتحميل الفيديوهات. أرسل رابط الفيديو.",
        "choose": "اختر اللغة:",
        "link": "أرسل رابط الفيديو.",
        "working": "⏳ جارٍ تحميل الفيديو...",
        "success": "✅ تم التحميل! شكراً لاستخدام @SaveToVid_bot!",
        "error": "❌ تعذر تحميل الفيديو. جرب رابطاً آخر.",
        "youtube_error": "تعذر تحميل فيديو YouTube. قد تكون هناك قيود من YouTube.",
        "button": "🎬 تحميل الفيديو",
        "group": "➕ أضف إلى المجموعة",
        "selected": "تم تغيير اللغة."
    }
}


# =============== MENYU ===============

def language_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    markup.row(
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    return markup


def main_keyboard(lang):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        TEXTS[lang]["group"],
        url="https://t.me/SaveToVid_bot?startgroup=true"
    ))
    return markup


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
        "Tilni tanlang / Choose language:",
        reply_markup=language_keyboard()
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def language_callback(call):
    lang = call.data.split("_", 1)[1]
    if lang not in TEXTS:
        return
    save_user(call.message.chat.id)
    set_lang(call.message.chat.id, lang)
    bot.answer_callback_query(call.id, TEXTS[lang]["selected"])
    bot.send_message(
        call.message.chat.id,
        TEXTS[lang]["welcome"],
        reply_markup=main_keyboard(lang)
    )


# =============== YUKLAB OLISH ===============

def extract_video(url, folder):
    output = os.path.join(folder, "%(title).80s-%(id)s.%(ext)s")
    options = {
        "outtmpl": output,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "max_filesize": MAX_FILE_SIZE,
        "socket_timeout": 25,
        "retries": 2,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

        if not os.path.exists(filepath):
            base = os.path.splitext(filepath)[0]
            candidates = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.startswith(os.path.basename(base))
            ]
            if candidates:
                filepath = candidates[0]

        if not os.path.isfile(filepath):
            raise FileNotFoundError("Video fayli topilmadi")

        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            raise ValueError("Video hajmi 49 MB dan katta")

        return filepath


def download_and_send(chat_id, url, status_message_id):
    folder = tempfile.mkdtemp(prefix="video_")
    try:
        with download_lock:
            filepath = extract_video(url, folder)

            bot.edit_message_text(
                "⏳ Video/MP4 yuklab olinmoqda...",
                chat_id,
                status_message_id
            )

            with open(filepath, "rb") as video:
                bot.send_video(
                    chat_id,
                    video,
                    supports_streaming=True,
                    caption="🎬 @SaveToVid_bot"
                )

            lang = get_lang(chat_id)
            bot.send_message(chat_id, TEXTS[lang]["success"])

    except Exception as error:
        logging.exception("Download error: %s", error)
        lang = get_lang(chat_id)
        text = TEXTS[lang]["error"]
        if "youtube.com" in url or "youtu.be" in url:
            text = TEXTS[lang]["youtube_error"]
        try:
            bot.send_message(chat_id, text)
        except Exception:
            pass
    finally:
        # Telegram'ga yuborilgan yoki xatolik yuz bergan bo'lsa ham
        # vaqtinchalik papka va undagi fayllar o'chiriladi.
        shutil.rmtree(folder, ignore_errors=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("download_"))
def download_callback(call):
    key = call.data.replace("download_", "", 1)
    item = pending_downloads.pop(key, None)

    if not item:
        bot.answer_callback_query(call.id, "Havola muddati tugagan.")
        return

    bot.answer_callback_query(call.id)
    status = bot.send_message(
        call.message.chat.id,
        TEXTS[get_lang(call.message.chat.id)]["working"]
    )

    thread = threading.Thread(
        target=download_and_send,
        args=(call.message.chat.id, item, status.message_id),
        daemon=True
    )
    thread.start()


# =============== HAVOLALAR ===============

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


@bot.message_handler(content_types=["text"], func=lambda m: m.chat.type == "private")
def private_text(message):
    save_user(message.chat.id)
    lang = get_lang(message.chat.id)

    if message.chat.id in broadcast_waiting:
        broadcast_waiting.remove(message.chat.id)
        broadcast(message)
        return

    match = URL_RE.search(message.text or "")
    if not match:
        bot.reply_to(message, TEXTS[lang]["link"])
        return

    url = match.group(0).rstrip(".,)")
    key = uuid.uuid4().hex[:12]
    pending_downloads[key] = url

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        TEXTS[lang]["button"],
        callback_data=f"download_{key}"
    ))
    bot.reply_to(message, "Havola qabul qilindi:", reply_markup=markup)


# =============== ADMIN BUYRUQLARI ===============

def is_admin(message):
    return message.from_user and message.from_user.id == ADMIN_ID


@bot.message_handler(commands=["stats"])
def stats(message):
    if not is_admin(message):
        return

    with db_lock:
        conn = db()
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        groups = conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        conn.close()

    bot.reply_to(
        message,
        f"📊 Bot statistikasi\n\n👤 Foydalanuvchilar: {users}\n👥 Guruhlar: {groups}"
    )


@bot.message_handler(commands=["send"])
def send_command(message):
    if not is_admin(message):
        return
    broadcast_waiting.add(message.chat.id)
    bot.reply_to(message, "Yuboriladigan matn yoki rasmni jo‘nating. Bekor qilish: /cancel")


@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if message.chat.id in broadcast_waiting:
        broadcast_waiting.discard(message.chat.id)
        bot.reply_to(message, "Bekor qilindi.")


def broadcast(message):
    with db_lock:
        conn = db()
        targets = [x[0] for x in conn.execute(
            "SELECT chat_id FROM users"
        ).fetchall()]
        targets += [x[0] for x in conn.execute(
            "SELECT chat_id FROM chats"
        ).fetchall()]
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
            time.sleep(0.04)
        except Exception:
            continue

    bot.send_message(message.chat.id, f"✅ Yuborildi: {sent} ta chat")


# =============== GURUH FUNKSIYALARI ===============

@bot.message_handler(content_types=["new_chat_members"])
def new_members(message):
    save_chat(message.chat.id, message.chat.type)
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass


@bot.message_handler(content_types=["left_chat_member"])
def left_member(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass


@bot.message_handler(
    content_types=["text"],
    func=lambda m: m.chat.type in ["group", "supergroup"]
)
def group_moderation(message):
    save_chat(message.chat.id, message.chat.type)

    if message.from_user and message.from_user.id == ADMIN_ID:
        return

    # Havolali reklama xabarlarini o'chirish.
    if URL_RE.search(message.text or ""):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass


# =============== SERVER ===============

@app.route("/")
def home():
    return "Bot ishlayapti!"


@app.route("/health")
def health():
    return "OK"


def run_flask():
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("Bot ishga tushdi")
    bot.infinity_polling(skip_pending=True, timeout=30)
