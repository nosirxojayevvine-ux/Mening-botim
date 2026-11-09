import os
import threading
from flask import Flask
import telebot
from telebot import types

# --- RENDER UCHUN FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Tokenni Render muhitidan (Environment Variables) xavfsiz o'qib oladi
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8019481444  # Sizning ID raqamingiz

bot = telebot.TeleBot(TOKEN)

user_languages = {}
total_users = set()
total_downloads = 0

# --- 5 TA TILDAGI MATNLAR ---
LANG_DATA = {
    "uz": {
        "welcome": (
            "🔥 **Assalomu alaykum.**\n"
            "@Mening_botim ga Xush kelibsiz.\n"
            "Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
            "• **Instagram** - post, stories, reels + audio bilan;\n"
            "• **TikTok** - suv belgisiz video + audio bilan;\n"
            "• **YouTube** - videolar va shorts + audio bilan;\n"
            "• **Snapchat** - suv belgisiz video + audio bilan;\n"
            "• **Likee** - suv belgisiz video + audio bilan;\n"
            "• **Pinterest** - suv belgisiz video va rasmlar + audio bilan;\n"
            "• **Threads** - video va rasmlar + audio bilan;\n\n"
            "🚀 **Yuklab olmoqchi bo'lgan videoga havolani yuboring!**\n"
            "😎 **Bot guruhlarda ham ishlay oladi!**"
        ),
        "choose_success": "🇺🇿 Til O'zbek tiliga o'zgartirildi. Endi havola yuboring:",
        "yt_error": (
            "💡 **Lekin bu bizning aybimiz emas!**\n"
            "Bunda YouTube o'z xavfsizligini kuchaytirgani sababli, afsuski, "
            "bu videoni yuklab ololmadik. Bizni tushunganingizdan umiddamiz! 🙏"
        ),
        "success": (
            "✅ **Yuklab olindi!**\n\n"
            "Yuborgan linkingiz uchun @Mening_botim nomidan sizga rahmat, "
            "kelasi linkni yuklab berishga tayyormiz! 🚀\n\n"
            "--- \n"
            "✨ **Bizning qo'shimcha imkoniyatimiz:**\n"
            "Guruhingizni tartibli saqlang! Kirdi-chiqdi va reklamalarni "
            "avtomatik o'chiruvchi qulay yordamchi botni guruhingizga qo'shing 👇"
        ),
        "add_group": "➕ Guruhga qo'shish"
    },
    "uz_kr": {
        "welcome": (
            "🔥 **Ассалому алайкум.**\n"
            "@Mening_botim га Хуш келибсиз.\n"
            "Бот орқали қуйидагиларни юклаб олишингиз мумкин:\n\n"
            "• **Instagram** - пост, stories, reels + аудио билан;\n"
            "• **TikTok** - сув белгисиз видео + аудио билан;\n"
            "• **YouTube** - видеолар ва shorts + аудио билан;\n"
            "• **Snapchat** - сув белгисиз видео + аудио билан;\n"
            "• **Likee** - сув белгисиз видео + аудио билан;\n"
            "• **Pinterest** - сув белгисиз видео ва расмлар + аудио билан;\n"
            "• **Threads** - видео ва расмлар + аудио билан;\n\n"
            "🚀 **Юклаб демоқчи бўлган видеога ҳаволани юборинг!**\n"
            "😎 **Бот гуруҳларда ҳам ишлай олади!**"
        ),
        "choose_success": "🇺🇿 Тил Ўзбекчага ўзгартирилди. Энди ҳавола юборинг:",
        "yt_error": (
            "💡 **Лекин бу бизнинг айбимиз эмас!**\n"
            "Бунда YouTube ўз хавфсизлигини кучайтиргани сабабли, афсуски, "
            "бу видеони юклаб ололмадик. Бизни тушурганингиздан умиддамиз! 🙏"
        ),
        "success": (
            "✅ **Юклаб олинди!**\n\n"
            "Юборган линкингиз учун @Mening_botim номидан сизга раҳмат, "
            "келаси линкини юклаб беришга тайёрмиз! 🚀\n\n"
            "--- \n"
            "✨ **Бизнинг қўшимча имкониятимиз:**\n"
            "Гуруҳингизни тартибли сақланг! Кирди-чиқди ва рекламаларни "
            "автоматик ўчирувчи қулай ёрдамчи ботни гуруҳингизни қўшинг 👇"
        ),
        "add_group": "➕ Гуруҳга қўшиш"
    },
    "ru": {
        "welcome": (
            "🔥 **Здравствуйте.**\n"
            "Добро пожаловать в @Mening_botim.\n"
            "Через бота вы можете скачать следующее:\n\n"
            "• **Instagram** - пост, stories, reels + аудио;\n"
            "• **TikTok** - видео без водяного знака + аудио;\n"
            "• **YouTube** - видео и shorts + аудио;\n"
            "• **Snapchat** - видео без водяного знака + аудио;\n"
            "• **Likee** - видео без водяного знака + аудио;\n"
            "• **Pinterest** - видео и фото без водяного знака + аудио;\n"
            "• **Threads** - видео и фото + аудио;\n\n"
            "🚀 **Отправьте ссылку на видео, которое хотите скачать!**\n"
            "😎 **Бот также работает в группах!**"
        ),
        "choose_success": "🇷🇺 Язык изменен на Русский. Отправьте ссылку:",
        "yt_error": (
            "💡 **Но это не наша вина!**\n"
            "Из-за усиления безопасности YouTube
