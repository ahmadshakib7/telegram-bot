import os
import logging
from flask import Flask, request
import requests as http_requests

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')

# Flask app
app = Flask(__name__)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, parse_mode='HTML'):
    """Send message via Telegram Bot API"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    try:
        response = http_requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def send_chat_action(chat_id, action='typing'):
    """Send chat action (typing indicator)"""
    url = f"{TELEGRAM_API}/sendChatAction"
    payload = {'chat_id': chat_id, 'action': action}
    try:
        http_requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error sending chat action: {e}")

def chat_with_groq(user_message):
    """Chat with Groq AI"""
    try:
        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'messages': [
                {'role': 'system', 'content': 'You are a helpful AI assistant. Respond in the same language as the user.'},
                {'role': 'user', 'content': user_message}
            ],
            'model': 'llama3-8b-8192', 'temperature': 0.7, 'max_tokens': 1024
        }
        response = http_requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers, json=payload, timeout=30
        )
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            logger.error(f"Groq error: {data}")
            return "â Ø®Ø·Ø§ Ø¯Ø± Ù¾Ø±Ø¯Ø§Ø²Ø´ Ù¾ÛØ§Ù!"
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "â Ø®Ø·Ø§ Ø¯Ø± Ù¾Ø±Ø¯Ø§Ø²Ø´ Ù¾ÛØ§Ù! ÙØ·ÙØ§Ù Ø¯ÙØ¨Ø§Ø±Ù ØªÙØ§Ø´ Ú©ÙÛØ¯."

def get_football_info():
    """Get football leagues info"""
    try:
        url = "https://v3.football.api-sports.io/leagues"
        headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        response = http_requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data.get('response'):
            text = "â½ <b>ÙÛÚ¯âÙØ§Û ÙØ¹Ø±ÙÙ:</b>\n\n"
            for league in data['response'][:5]:
                text += f"â¢ {league['league']['name']} ({league['country']['name']})\n"
            return text
        return "â Ø§Ø·ÙØ§Ø¹Ø§ØªÛ ÛØ§ÙØª ÙØ´Ø¯!"
    except Exception as e:
        logger.error(f"Football API error: {e}")
        return "â Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø±ÛØ§ÙØª Ø§Ø·ÙØ§Ø¹Ø§Øª ÙÙØªØ¨Ø§Ù!"

def download_video(video_url):
    """Download video using Cobalt API"""
    try:
        api_url = "https://api.cobalt.tools/api/json"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            'url': video_url,
            'isAudioOnly': False
        }
        response = http_requests.post(api_url, headers=headers, json=payload, timeout=60)
        data = response.json()

        if data.get('status') == 'tunnel':
            return {'success': True, 'url': data['url']}
        elif data.get('status') == 'picker':
            return {'success': True, 'url': data['picker'][0]['url']}
        elif data.get('status') == 'error':
            return {'success': False, 'error': data.get('text', 'Unknown error')}
        else:
            return {'success': False, 'error': 'Unknown response from server'}
    except Exception as e:
        logger.error(f"Download error: {e}")
        return {'success': False, 'error': str(e)}

# ========== ROUTES ==========

@app.route('/')
def index():
    return 'AS AI Assistant Bot is running! ð¤'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set webhook URL"""
    webhook_url = f"https://{request.host}/webhook"
    url = f"{TELEGRAM_API}/setWebhook"
    try:
        response = http_requests.post(url, json={'url': webhook_url})
        result = response.json()
        if result.get('ok'):
            return f'â Webhook set: {webhook_url}', 200
        return f'â Error: {result}', 500
    except Exception as e:
        return f'â Error: {e}', 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram"""
    try:
        update = request.get_json(force=True)
        logger.info(f"Received update: {update}")

        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            # Send typing indicator
            send_chat_action(chat_id, 'typing')

            # Handle commands
            if text == '/start':
                welcome_text = """ð¤ <b>AS AI Assistant</b> - Ø®ÙØ´ Ø¢ÙØ¯ÛØ¯!

ÙÙ ÛÙ Ø¯Ø³ØªÛØ§Ø± ÙÙØ´ÙÙØ¯Ù Ú©Ù ÙÛâØªÙÙÙ:
â¢ ð¬ ÚØª ÙÙØ´ÙÙØ¯ Ø¨Ø§ AI
â¢ â½ Ø§Ø·ÙØ§Ø¹Ø§Øª ÙÙØªØ¨Ø§Ù
â¢ â¬ï¸ Ø¯Ø§ÙÙÙØ¯ ÙÛØ¯ÛÙ Ø§Ø² YouTube, Instagram, TikTok, Twitter

<b>Ø¯Ø³ØªÙØ±Ø§Øª:</b>
/start - Ø´Ø±ÙØ¹
/help - Ø±Ø§ÙÙÙØ§
/football - Ø§Ø·ÙØ§Ø¹Ø§Øª ÙÙØªØ¨Ø§Ù
/download [URL] - Ø¯Ø§ÙÙÙØ¯ ÙÛØ¯ÛÙ

ð¡ ÙØ± Ù¾ÛØ§ÙÛ Ø¨ÙØ±Ø³ØªÛØ AI Ø¬ÙØ§Ø¨ ÙÛØ¯Ù!"""
                send_message(chat_id, welcome_text)

            elif text == '/help':
                help_text = """ð <b>Ø±Ø§ÙÙÙØ§Û Ø¯Ø³ØªÙØ±Ø§Øª:</b>

/start - Ø´Ø±ÙØ¹ Ø¨Ø§Øª
/help - ÙÙÛÙ Ø±Ø§ÙÙÙØ§
/football - Ø§Ø·ÙØ§Ø¹Ø§Øª ÙÙØªØ¨Ø§Ù
/download [URL] - Ø¯Ø§ÙÙÙØ¯ ÙÛØ¯ÛÙ

ð¡ <b>ÙÚ©ØªÙ:</b>
ÙØ± Ù¾ÛØ§ÙÛ Ø¨ÙØ±Ø³ØªÛØ AI Ø¬ÙØ§Ø¨ ÙÛØ¯Ù!

<b>ÙØ«Ø§Ù Ø¯Ø§ÙÙÙØ¯:</b>
/download https://www.instagram.com/reel/..."""
                send_message(chat_id, help_text)

            elif text == '/football':
                send_message(chat_id, get_football_info())

            elif text.startswith('/download'):
                parts = text.split(' ', 1)
                if len(parts) < 2:
                    send_message(chat_id, "â¬ï¸ <b>ÙØ­ÙÙ Ø§Ø³ØªÙØ§Ø¯Ù:</b>\n/download [URL]\n\n<b>ÙØ«Ø§Ù:</b>\n/download https://www.instagram.com/reel/...")
                else:
                    video_url = parts[1].strip()
                    send_chat_action(chat_id, 'upload_document')
                    send_message(chat_id, "â³ Ø¯Ø± Ø­Ø§Ù Ù¾Ø±Ø¯Ø§Ø²Ø´ ÙÛÙÚ©...")

                    result = download_video(video_url)
                    if result['success']:
                        download_url = result['url']
                        send_message(chat_id, f"â <b>ÙÛØ¯ÛÙ Ø¢ÙØ§Ø¯Ù Ø¯Ø§ÙÙÙØ¯!</b>\n\n<a href='{download_url}'>â¬ï¸ Ú©ÙÛÚ© Ú©ÙÛØ¯ Ø¨Ø±Ø§Û Ø¯Ø§ÙÙÙØ¯</a>\n\nâ ï¸ Ø§Ú¯Ù ÙÛÙÚ© Ú©Ø§Ø± ÙÚ©Ø±Ø¯Ø Û±Û° Ø«Ø§ÙÛÙ ØµØ¨Ø± Ú©ÙÛØ¯ Ù Ø¯ÙØ¨Ø§Ø±Ù Ø§ÙØªØ­Ø§Ù Ú©ÙÛØ¯.")
                    else:
                        send_message(chat_id, f"â <b>Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø§ÙÙÙØ¯:</b>\n{result['error']}\n\nð¡ ÙÚ©ØªÙ: Cobalt API ÙÙÚ©ÙÙ Ø¨Ø¹Ø¶Û ÙÛÙÚ©âÙØ§ Ø±Ù Ù¾Ø´ØªÛØ¨Ø§ÙÛ ÙÚ©ÙÙ.")

            else:
                # Chat with AI
                response = chat_with_groq(text)
                send_message(chat_id, response)

        return 'OK', 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
