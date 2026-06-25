import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')

app = Flask(__name__)
groq_client = Groq(api_key=GROQ_API_KEY)
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "🤖 AS AI Assistant - خوش آمدید!

من یه دستیار هوشمندم!

دستورات:
/start - شروع
/help - راهنما
/football - فوتبال"
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "📚 راهنما:

/start - شروع
/help - راهنما
/football - فوتبال

💡 هر پیامی بفرستی، AI جواب میده!"
    await update.message.reply_text(help_text)

async def football_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://v3.football.api-sports.io/leagues"
        headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get('response'):
            leagues = data['response'][:5]
            text = "⚽ لیگ‌های معروف:

"
            for league in leagues:
                text += f"• {league['league']['name']} ({league['country']['name']})
"
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("❌ اطلاعاتی یافت نشد!")
    except Exception as e:
        logger.error(f"Football API error: {e}")
        await update.message.reply_text("❌ خطا در دریافت اطلاعات فوتبال!")

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Respond in the same language as the user."},
                {"role": "user", "content": user_message}
            ],
            model="llama3-8b-8192", temperature=0.7, max_tokens=1024
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        await update.message.reply_text("❌ خطا در پردازش پیام!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("football", football_info))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_ai))
application.add_error_handler(error_handler)

@app.route('/')
def index():
    return 'AS AI Assistant Bot is running! 🤖'

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK', 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"https://{request.host}/{BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)
    return f'Webhook set to: {webhook_url}', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
