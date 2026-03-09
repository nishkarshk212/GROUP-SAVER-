from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import asyncio

# Default settings
DEFAULT_SETTINGS = {
    "nsfw_detection": True,
    "report_admins": False,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "settings" not in context.chat_data:
        context.chat_data["settings"] = DEFAULT_SETTINGS.copy()

    msg = await update.message.reply_text("🔄 Starting NSFW Detector...")

    steps = [
        "🔄 Starting NSFW Detector...\n\n⚙ Loading AI model...",
        "🔄 Starting NSFW Detector...\n\n⚙ Loading AI model...\n📂 Preparing scanner...",
        "🔄 Starting NSFW Detector...\n\n⚙ Loading AI model...\n📂 Preparing scanner...\n🛡 Activating protection...",
        "✅ NSFW Detector Bot Ready!\n\nSend an image to scan."
    ]

    for step in steps:
        await asyncio.sleep(1)
        await msg.edit_text(step)

    settings = context.chat_data["settings"]
    keyboard = [
        [InlineKeyboardButton(f"NSFW Detection: {'✅' if settings['nsfw_detection'] else '❌'}", callback_data="toggle_nsfw_detection")],
        [InlineKeyboardButton(f"Report Admins: {'✅' if settings['report_admins'] else '❌'}", callback_data="toggle_report_admins")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Bot Settings:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "toggle_nsfw_detection":
        context.chat_data["settings"]["nsfw_detection"] = not context.chat_data["settings"]["nsfw_detection"]
    elif query.data == "toggle_report_admins":
        context.chat_data["settings"]["report_admins"] = not context.chat_data["settings"]["report_admins"]

    settings = context.chat_data["settings"]
    keyboard = [
        [InlineKeyboardButton(f"NSFW Detection: {'✅' if settings['nsfw_detection'] else '❌'}", callback_data="toggle_nsfw_detection")],
        [InlineKeyboardButton(f"Report Admins: {'✅' if settings['report_admins'] else '❌'}", callback_data="toggle_report_admins")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="⚙️ Bot Settings:", reply_markup=reply_markup) 

app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build() 

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()