import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_ID
import os

DATA_FILE = "data.json"

# States
LANGUAGE, SELECT_TYPE, AWAITING_CODE = range(3)
ADMIN_SELECT_TYPE, ADMIN_WAIT_IMAGE, ADMIN_WAIT_TEXT, ADMIN_WAIT_CODE = range(10, 14)
ADMIN_DELETE_CODE = 20

user_lang = {}
user_category = {}
admin_temp = {}

# JSON helpers
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_back_button(lang):
    return {
        "uz": "⬅️ Orqaga",
        "ru": "⬅️ Назад",
        "en": "⬅️ Back"
    }.get(lang, "⬅️ Back")

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇺🇿 O'zbek", "🇷🇺 Русский", "🇬🇧 English"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=markup
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    if "🇺🇿" in text or "O'zbek" in text.lower():
        user_lang[user_id] = "uz"
    elif "🇷🇺" in text or "Русский" in text or "рус" in text.lower():
        user_lang[user_id] = "ru"
    elif "🇬🇧" in text or "English" in text.lower():
        user_lang[user_id] = "en"
    else:
        await update.message.reply_text("❗️Iltimos, tugmalardan birini tanlang.")
        return LANGUAGE

    lang = user_lang[user_id]
    keyboard = [["🎬 Kino", "🎌 Anime"], [get_back_button(lang)]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text({
        "uz": "Tanlang: Kino yoki Anime?",
        "ru": "Выберите: Фильм или Аниме?",
        "en": "Choose: Movie or Anime?",
    }[lang], reply_markup=markup)
    return SELECT_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.message.from_user.id
    lang = user_lang.get(user_id, "en")

    if text in ["⬅️ orqaga", "⬅️ назад", "⬅️ back"]:
        return await start(update, context)

    if "kino" in text or "movie" in text:
        user_category[user_id] = "kino"
    elif "anime" in text:
        user_category[user_id] = "anime"
    else:
        await update.message.reply_text("❗️Iltimos, Kino yoki Anime ni tanlang.")
        return SELECT_TYPE

    keyboard = [[get_back_button(lang)]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text({
        "uz": "Kod kiriting:",
        "ru": "Введите код:",
        "en": "Enter the code:"
    }[lang], reply_markup=markup)
    return AWAITING_CODE

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    user_id = update.message.from_user.id
    lang = user_lang.get(user_id, "en")

    if code.lower() in ["⬅️ orqaga", "⬅️ назад", "⬅️ back"]:
        keyboard = [["🎬 Kino", "🎌 Anime"], [get_back_button(lang)]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text({
            "uz": "Tanlang: Kino yoki Anime?",
            "ru": "Выберите: Фильм или Аниме?",
            "en": "Choose: Movie or Anime:",
        }[lang], reply_markup=markup)
        return SELECT_TYPE

    data = load_data()
    category = user_category.get(user_id, "kino")
    full_code = f"{category}_{code}"

    if full_code in data:
        entry = data[full_code]
        await update.message.reply_photo(photo=entry["image"], caption=entry["text"])
    else:
        await update.message.reply_text({
            "uz": "❌ Bunday kod topilmadi.",
            "ru": "❌ Код не найден.",
            "en": "❌ Code not found."
        }[lang])
    return AWAITING_CODE

# Admin qo‘shish
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz.")
        return ConversationHandler.END
    keyboard = [["🎬 Kino", "🎌 Anime"]]
    await update.message.reply_text("🎯 Qaysi turdagi kontent qo‘shmoqchisiz?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ADMIN_SELECT_TYPE

async def admin_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "kino" in text:
        admin_temp["category"] = "kino"
    elif "anime" in text:
        admin_temp["category"] = "anime"
    else:
        await update.message.reply_text("❗️Iltimos, tugmadan tanlang.")
        return ADMIN_SELECT_TYPE
    await update.message.reply_text("📤 Rasm yuboring:")
    return ADMIN_WAIT_IMAGE

async def admin_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    admin_temp["image"] = photo.file_id
    await update.message.reply_text("📝 Matn kiriting:")
    return ADMIN_WAIT_TEXT

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_temp["text"] = update.message.text
    await update.message.reply_text("🔢 Kod kiriting (masalan: naruto01):")
    return ADMIN_WAIT_CODE

async def admin_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    full_code = f'{admin_temp["category"]}_{code}'
    data = load_data()
    data[full_code] = {
        "image": admin_temp["image"],
        "text": admin_temp["text"]
    }
    save_data(data)
    await update.message.reply_text(f"✅ '{full_code}' kodi bilan saqlandi.")
    admin_temp.clear()
    return ConversationHandler.END

# Admin delete
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz.")
        return ConversationHandler.END
    await update.message.reply_text("❌ O‘chirmoqchi bo‘lgan kontent kodini kiriting (masalan: anime_naruto01):")
    return ADMIN_DELETE_CODE

async def admin_delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    data = load_data()
    if code in data:
        del data[code]
        save_data(data)
        await update.message.reply_text(f"🗑️ '{code}' kodi o‘chirildi.")
    else:
        await update.message.reply_text("❗️Kod topilmadi.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Foydalanuvchi oqimi
    user_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT, set_language)],
            SELECT_TYPE: [MessageHandler(filters.TEXT, select_type)],
            AWAITING_CODE: [MessageHandler(filters.TEXT, handle_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Admin qo‘shish
    admin_add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_command)],
        states={
            ADMIN_SELECT_TYPE: [MessageHandler(filters.TEXT, admin_select_type)],
            ADMIN_WAIT_IMAGE: [MessageHandler(filters.PHOTO, admin_image)],
            ADMIN_WAIT_TEXT: [MessageHandler(filters.TEXT, admin_text)],
            ADMIN_WAIT_CODE: [MessageHandler(filters.TEXT, admin_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Admin o‘chirish
    admin_delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_command)],
        states={
            ADMIN_DELETE_CODE: [MessageHandler(filters.TEXT, admin_delete_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(user_conv)
    app.add_handler(admin_add_conv)
    app.add_handler(admin_delete_conv)

    print("🤖 Bot ishga tushdi.")
    app.run_polling()

if __name__ == "__main__":
    main()
