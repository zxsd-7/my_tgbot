import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_ID

# States
LANGUAGE, SELECT_TYPE, AWAITING_CODE = range(3)
ADMIN_PANEL, ADMIN_SELECT_TYPE, ADMIN_WAIT_IMAGE, ADMIN_WAIT_TEXT, ADMIN_WAIT_CODE = range(10, 15)
ADMIN_DELETE_CODE = 20

# User & Admin context
user_lang = {}
user_category = {}
admin_temp = {}

DATA_FILE = "data.json"

# Helpers
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

# --- User flow ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇺🇿 O'zbek", "🇷🇺 Русский", "🇬🇧 English"]]
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.message.from_user.id

    if "uz" in text:
        user_lang[user_id] = "uz"
    elif "ru" in text:
        user_lang[user_id] = "ru"
    elif "en" in text:
        user_lang[user_id] = "en"
    else:
        return await update.message.reply_text("❗️Iltimos, tugmadan tanlang.")

    lang = user_lang[user_id]
    keyboard = [["🎬 Kino", "🎌 Anime"], [get_back_button(lang)]]
    await update.message.reply_text({
        "uz": "Tanlang: Kino yoki Anime?",
        "ru": "Выберите: Фильм или Аниме?",
        "en": "Choose: Movie or Anime?"
    }[lang], reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
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
        return await update.message.reply_text("❗️Kino yoki Anime ni tanlang.")

    await update.message.reply_text({
        "uz": "Kod kiriting:",
        "ru": "Введите код:",
        "en": "Enter the code:"
    }[lang])
    return AWAITING_CODE

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    user_id = update.message.from_user.id
    lang = user_lang.get(user_id, "en")
    category = user_category.get(user_id, "kino")
    full_code = f"{category}_{code}"

    data = load_data()
    if full_code in data:
        content = data[full_code]
        await update.message.reply_photo(photo=content["image"], caption=content["text"])
    else:
        await update.message.reply_text({
            "uz": "❌ Bunday kod topilmadi.",
            "ru": "❌ Код не найден.",
            "en": "❌ Code not found."
        }[lang])
    return AWAITING_CODE

# --- Admin Panel ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Siz admin emassiz.")
    
    keyboard = [
        ["➕ Kontent qo‘shish", "❌ Kontent o‘chirish"]
    ]
    await update.message.reply_text("🔐 Admin Panelga xush kelibsiz!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ADMIN_PANEL

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "qo‘shish" in text or "kontent qo" in text:
        await update.message.reply_text("🎬 Qaysi turdagi kontent qo‘shmoqchisiz? (Kino yoki Anime)", reply_markup=ReplyKeyboardMarkup([["Kino", "Anime"]], resize_keyboard=True))
        return ADMIN_SELECT_TYPE

    elif "o‘chirish" in text:
        await update.message.reply_text("🗑 Kodni kiriting (masalan: anime_naruto01):")
        return ADMIN_DELETE_CODE

    else:
        return await update.message.reply_text("❗️Noto‘g‘ri tanlov.")

async def admin_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "kino" in text:
        admin_temp["category"] = "kino"
    elif "anime" in text:
        admin_temp["category"] = "anime"
    else:
        return await update.message.reply_text("❗️Iltimos, tugmadan tanlang.")
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

async def admin_delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    data = load_data()
    if code in data:
        del data[code]
        save_data(data)
        await update.message.reply_text(f"🗑 '{code}' kodi o‘chirildi.")
    else:
        await update.message.reply_text("❗️Bunday kod topilmadi.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User handler
    user_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT, set_language)],
            SELECT_TYPE: [MessageHandler(filters.TEXT, select_type)],
            AWAITING_CODE: [MessageHandler(filters.TEXT, handle_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Admin panel
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            ADMIN_PANEL: [MessageHandler(filters.TEXT, handle_admin_panel)],
            ADMIN_SELECT_TYPE: [MessageHandler(filters.TEXT, admin_select_type)],
            ADMIN_WAIT_IMAGE: [MessageHandler(filters.PHOTO, admin_image)],
            ADMIN_WAIT_TEXT: [MessageHandler(filters.TEXT, admin_text)],
            ADMIN_WAIT_CODE: [MessageHandler(filters.TEXT, admin_code)],
            ADMIN_DELETE_CODE: [MessageHandler(filters.TEXT, admin_delete_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(user_conv)
    app.add_handler(admin_conv)

    print("✅ Bot ishga tushdi.")
    app.run_polling()

if __name__ == "__main__":
    main()
