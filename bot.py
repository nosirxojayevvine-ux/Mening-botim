import os
import threading
from flask import Flask
import telebot
from telebot import types

app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8019481444

bot = telebot.TeleBot(TOKEN)

user_languages = {}
total_users = set()
total_downloads = 0

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
            "Из-за усиления безопасности YouTube мы, к сожалению, "
            "не смогли скачать это видео. Надеемся на ваше понимание! 🙏"
        ),
        "success": (
            "✅ **Успешно скачано!**\n\n"
            "Спасибо за отправленную ссылку от лица @Mening_botim, "
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
            "Welcome to @Mening_botim.\n"
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
            "Thank you for your link from @Mening_botim, "
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
            "مرحباً بك في @Mening_botim.\n"
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
            "شكراً لإرسال الرابط نيابة عن @Mening_botim، "
            "نحن مستعدون لتنزيل الرابط التالي! 🚀\n\n"
            "--- \n"
            "✨ **ميزتنا الإضافية:**\n"
            "حافظ على نظام مجموعتك! أضف البوت الذي يحذف "
            "الإعلانات ورسائل الدخول والخروج تلقائياً 👇"
        ),
        "add_group": "➕ أضف إلى المجموعة"
    }
}

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
    markup.add(types.InlineKeyboardButton(text, url="https://t.me/Mening_botim?startgroup=true"))
    return markup

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
    
    bot.send_message(
        message.chat.id,
        multi_lang_intro,
        reply_markup=get_language_keyboard()
    )

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id == ADMIN_ID:
        text = f"📊 **Statistika:**\n\n👥 Foydalanuvchilar: {len(total_users)}\n📥 Yuklanganlar: {total_downloads}"
        bot.reply_to(message, text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "Bu buyruq faqat admin uchun! ❌")

@bot.message_handler(commands=['send'])
def broadcast_message(message):
    if message.from_user.id == ADMIN_ID:
        text_to_send = message.text.replace("/send", "").strip()
        if not text_to_send:
            bot.reply_to(message, "Assalomu alaykum! Tarqatish uchun matn yozing. Masalan: `/send Salom!`", parse_mode="Markdown")
            return
        
        success_count = 0
        for uid in total_users:
            try:
                bot.send_message(uid, f"Assalomu alaykum!\n\n{text_to_send}")
                success_count += 1
            except:
                pass
        bot.reply_to(message, f"Xabar {success_count} ta foydalanuvchiga yuborildi ✅")
    else:
        bot.reply_to(message, "Bu buyruq faqat admin uchun! ❌")

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_selection(call):
    user_id = call.from_user.id
    selected_lang = call.data.replace("lang_", "")
    user_languages[user_id] = selected_lang
    
    bot.answer_callback_query(call.id, "Til saqlandi!")
    
    bot.send_message(
        chat_id=call.message.chat.id,
        text=LANG_DATA[selected_lang]["choose_success"] + "\n\n" + LANG_DATA[selected_lang]["welcome"],
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_incoming_link(message):
    global total_downloads
    user_id = message.from_user.id
    total_users.add(user_id)
    lang = user_languages.get(user_id, "uz")
    
    text = message.text.lower()
    
    if "youtube.com" in text or "youtu.be" in text:
        bot.reply_to(message, LANG_DATA[lang]["yt_error"], parse_mode="Markdown")
    else:
        total_downloads += 1
        bot.reply_to(
            message,
            LANG_DATA[lang]["success"],
            reply_markup=get_success_keyboard(lang),
            parse_mode="Markdown"
        )

@bot.message_handler(content_types=['new_chat_members'])
def delete_join_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@bot.message_handler(content_types=['left_chat_member'])
def delete_left_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

if __name__ == '__main__':
    
