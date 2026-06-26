import os
import logging
from flask import Flask, request
import requests as http_requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')

app = Flask(__name__)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    try:
        response = http_requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

def chat_with_ai(user_message):
    try:
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://as-ai-bot.onrender.com',
            'X-Title': 'AS AI Assistant Bot'
        }
        payload = {
            'messages': [
                {'role': 'system', 'content': 'You are a helpful AI assistant. Respond in the same language as the user.'},
                {'role': 'user', 'content': user_message}
            ],
            'model': 'meta-llama/llama-3.1-8b-instruct:free',
            'temperature': 0.7,
            'max_tokens': 1024
        }
        response = http_requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            logger.error(f"OpenRouter error: {data}")
            return "❌ خطا در پردازش پیام!"
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return "❌ خطا در پردازش پیام! لطفاً دوباره تلاش کنید."

def get_football_info():
    try:
        url = "https://v3.football.api-sports.io/leagues"
        headers = {
            'x-rapidapi-key': FOOTBALL_API_KEY,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        response = http_requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data.get('response'):
            text = "⚽ لیگ‌های معروف:\n\n"
            for league in data['response'][:5]:
                text += f"• {league['league']['name']} ({league['country']['name']})\n"
            return text
        return "❌ اطلاعاتی یافت نشد!"
    except Exception as e:
        logger.error(f"Football error: {e}")
        return "❌ خطا در دریافت اطلاعات فوتبال!"

@app.route('/')
def index():
    return 'AS AI Assistant Bot is running! 🤖'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"{TELEGRAM_API}/setWebhook"
    try:
        response = http_requests.post(url, json={'url': webhook_url})
        result = response.json()
        if result.get('ok'):
            return f'✅ Webhook set: {webhook_url}', 200
        return f'❌ Error: {result}', 500
    except Exception as e:
        return f'❌ Error: {e}', 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json(force=True)
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            if text == '/start':
                send_message(chat_id, "🤖 AS AI Assistant - خوش آمدید!\n\nدستورات:\n/start - شروع\n/help - راهنما\n/football - فوتبال")
            elif text == '/help':
                send_message(chat_id, "📚 راهنما:\n\n/start - شروع\n/help - راهنما\n/football - فوتبال\n\n💡 هر پیامی بفرستی، AI جواب میده!")
            elif text == '/football':
                send_message(chat_id, get_football_info())
            else:
                send_message(chat_id, chat_with_ai(text))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
