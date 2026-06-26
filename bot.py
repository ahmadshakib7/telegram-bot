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

# Video platforms
VIDEO_PLATFORMS = [
    'instagram.com', 'youtube.com', 'youtu.be', 'tiktok.com',
    'twitter.com', 'x.com', 'facebook.com', 'fb.watch',
    'reddit.com', 'vimeo.com', 'dailymotion.com'
]

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

def is_video_url(text):
    """Check if text contains a video URL"""
    text_lower = text.lower()
    return any(platform in text_lower for platform in VIDEO_PLATFORMS)

def extract_url(text):
    """Extract URL from text"""
    words = text.split()
    for word in words:
        if word.startswith('http://') or word.startswith('https://'):
            return word
    return text.strip()

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
            return "❌ خطا در پردازش پیام!"
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "❌ خطا در پردازش پیام! لطفاً دوباره تلاش کنید."

def get_football_info():
    """Get football leagues info"""
    try:
        url = "https://v3.football.api-sports.io/leagues"
        headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
        response = http_requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data.get('response'):
            text = "⚽ <b>لیگ‌های معروف:</b>\n\n"
            for league in data['response'][:5]:
                text += f"• {league['league']['name']} ({league['country']['name']})\n"
            return text
        return "❌ اطلاعاتی یافت نشد!"
    except Exception as e:
        logger.error(f"Football API error: {e}")
        return "❌ خطا در دریافت اطلاعات فوتبال!"

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
    return 'AS AI Assistant Bot is running! 🤖'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set webhook URL"""
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
    """Handle incoming webhook updates from Telegram"""
    try:
        update = request.get_json(force=True)
        logger.info(f"Received update: {update}")
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            # Check if message is a video URL
            video_url = None
            if is_video_url(text):
                video_url = extract_url(text)
            elif text.startswith('/download'):
                parts = text.split(' ', 1)
                if len(parts) > 1:
                    video_url = parts[1].strip()
            
            # Handle commands and messages
            if text == '/start':
                welcome_text = """🤖 <b>AS AI Assistant</b> - خوش آمدید!

من یه دستیار هوشمندم که می‌تونم:
• 💬 چت هوشمند با AI
• ⚽ اطلاعات فوتبال
• ⬇️ دانلود ویدیو از YouTube, Instagram, TikTok, Twitter

<b>دستورات:</b>
/start - شروع
/help - راهنما
/football - اطلاعات فوتبال

💡 <b>نکته:</b>
هر پیامی بفرستی، AI جواب میده!
ویدیو هم مستقیم بفرستی، دانلودش میکنم!"""
                send_message(chat_id, welcome_text)
                
            elif text == '/help':
                help_text = """📚 <b>راهنمای دستورات:</b>

/start - شروع بات
/help - همین راهنما
/football - اطلاعات فوتبال

💡 <b>نکته:</b>
هر پیامی بفرستی، AI جواب میده!

<b>دانلود ویدیو:</b>
فقط لینک ویدیو رو بفرست:
• Instagram Reels/Posts
• YouTube videos
• TikTok videos
• Twitter/X videos

یا از دستور:
/download [URL]"""
                send_message(chat_id, help_text)
                
            elif text == '/football':
                send_message(chat_id, get_football_info())
                
            elif video_url:
                # Download video
                send_chat_action(chat_id, 'upload_document')
                send_message(chat_id, "⏳ در حال پردازش لینک...")
                
                result = download_video(video_url)
                if result['success']:
                    download_url = result['url']
                    send_message(chat_id, f"✅ <b>ویدیو آماده دانلود!</b>\n\n<a href='{download_url}'>⬇️ کلیک کنید برای دانلود</a>\n\n⚠️ اگه لینک کار نکرد، ۱۰ ثانیه صبر کنید و دوباره امتحان کنید.")
                else:
                    send_message(chat_id, f"❌ <b>خطا در دانلود:</b>\n{result['error']}\n\n💡 نکته: Cobalt API ممکنه بعضی لینک‌ها رو پشتیبانی نکنه.")
                
            else:
                # Chat with AI
                send_chat_action(chat_id, 'typing')
                response = chat_with_groq(text)
                send_message(chat_id, response)
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
