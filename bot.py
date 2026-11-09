import os
import telebot
from telebot import types

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
            "@SaveToVid_bot ga Xush kelibsiz.\n"
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
            "Yuborgan linkingiz uchun @SaveToVideoBot nomidan sizga rahmat, "
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
            "@SaveToVid_bot га Хуш келибсиз.\n"
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
            "Юборган линкингиз учун @SaveToVideoBot номидан сизга раҳмат, "
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
            "Добро пожаловать в @SaveToVid_bot.\n"
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
            "Из-за усиления безопасности YouTube мы, к сожалению, "
            "не смогли скачать это видео. Надеемся на ваше понимание! 🙏"
        ),
        "success": (
            "✅ **Успешно скачано!**\n\n"
            "Спасибо за отправленную ссылку от лица @SaveToVideoBot, "
            "мы готовы скачать следующий файл! 🚀\n\n"
            "--- \n"
            "✨ **Наши дополнительные возможности:**\n"
            "Держите группу в порядке! Добавьте удобного бота, "
            "который удаляет рекламу и сообщения о входе/выходе 👇"
        ),
        "add_group": "➕ Добавить в группу"
    },
    "en": {
        "welcome": (
            "🔥 **Hello.**\n"
            "Welcome to @SaveToVid_bot.\n"
            "You can download the following via the bot:\n\n"
            "• **Instagram** - post, stories, reels + audio;\n"
            "• **TikTok** - video without watermark + audio;\n"
            "• **YouTube** - videos and shorts + audio;\n"
            "• **Snapchat** - video without watermark + audio;\n"
            "• **Likee** - video without watermark + audio;\n"
            "• **Pinterest** - video and photos + audio;\n"
            "• **Threads** - video and photos + audio;\n\n"
            "🚀 **Send the link of the video you want to download!**\n"
            "😎 **The bot also works in groups!**"
        ),
        "choose_success": "🇬🇧 Language changed to English. Send a link:",
        "yt_error": (
            "💡 **But this is not our fault!**\n"
            "Due to YouTube's enhanced security measures, we were unfortunately "
            "unable to download this video. We hope for your understanding! 🙏"
        ),
        "success": (
            "✅ **Downloaded successfully!**\n\n"
            "Thank you for your link from @SaveToVideoBot, "
            "we are ready to process your next request! 🚀\n\n"
            "--- \n"
            "✨ **Our extra feature:**\n"
            "Keep your group clean and tidy! Add our smart bot "
            "to automatically remove ads and join/leave notifications 👇"
        ),
        "add_group": "➕ Add to Group"
    },
    "ar": {
        "welcome": (
            "🔥 **أهلاً بك.**\n"
            "مرحباً بك في @SaveToVid_bot.\n"
            "يمكنك تنزيل ما يلي عبر البوت:\n\n"
            "• **Instagram** - منشور، قصص، ريلز + صوت;\n"
            "• **TikTok** - فيديو بدون علامة مائية + صوت;\n"
            "• **YouTube** - فيديوهات وشورتس + صوت;\n"
            "• **Snapchat** - فيديو بدون علامة مائية + صوت;\n"
            "• **Likee** - فيديو بدون علامة مائية + صوت;\n"
            "• **Pinterest** - فيديو وصور + صوت;\n"
            "• **Threads** - فيديو وصور + صوت;\n\n"
            "🚀 **أرسل رابط الفيديو الذي تريد تنزيله!**\n"
            "😎 **البوت يعمل أيضاً في المجموعات!**"
        ),
        "choose_success": "🇸🇦 تم تغيير اللغة إلى العربية. أرسل الرابط الآن:",
        "yt_error": (
            "💡 **ولكن هذا ليس خطأنا!**\n"
            "بسبب تشديد إجراءات الأمان في YouTube، لم نتمكن للأسف "
            "من تنزيل هذا الفيديو. نأمل تفهمكم! 🙏"
        ),
        "success": (
            "✅ **تم التنزيل بنجاح!**\n\n"
            "شكراً لإرسال الرابط نيابة عن @SaveToVideoBot، "
            "نحن مستعدون لتنزيل الرابط التالي! 🚀\n\n"
            "--- \n"
            "✨ **ميزتنا الإضافية:**\n"
            "حافظ على نظام مجموعتك! أضف البوت الذي يحذف "
            "الإعلانات ورسائل الدخول والخروج تلقائياً 👇"
        ),
        "add_group": "➕ أضف إلى المجموعة"
    }
}

# --- TUGMALAR ---
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

def get_success_keyboard(lang_code):
    markup = types.InlineKeyboardMarkup()
    text = LANG_DATA[lang_code]["add_group"]
    markup.add(types.InlineKeyboardButton(text, url="https://t.me/SaveToVid_bot?startgroup=true"))
    return markup

# --- START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    total_users.add(user_id)
    
    multi_lang_intro = (
        "O'zingizga qulay tilni tanlang 🇺🇿\n"
        "Ўзингизга қулай тилни танланг 🇺🇿\n"
        "Выбери язык, который тебе нравится 🇷🇺\n"
        "Choose the language you like 🇬🇧\n"
        "اختر لغتك المفضلة 🇸🇦"
    )
    
    bot.send_message
