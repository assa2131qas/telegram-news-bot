import feedparser
import asyncio
import emoji
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher

# === НАСТРОЙКИ ===
TOKEN = AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c  # Вставь токен из BotFather
RSS_URL = "https://cryptopanic.com/news/rss/?filter=important&currencies=BTC,ETH"
CHANNEL_ID = "-1002447063110"  # Или Chat ID, если канал приватный

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Список отправленных новостей (чтобы не дублировать)
sent_news = set()

def translate_text(text):
    """Переводит текст на иврит через бесплатный Google Translate"""
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        return f"Ошибка перевода: {e}"

def add_emojis(text):
    """Добавляет смайлики в зависимости от содержания новости"""
    emoji_dict = {
        "Bitcoin": "₿", "BTC": "₿", "биткоин": "₿",
        "Ethereum": "Ξ", "ETH": "Ξ",
        "рост": "📈", "падение": "📉",
        "рынок": "📊", "новость": "📰",
        "инвестиции": "💰", "прогноз": "🔮",
        "SEC": "⚖️", "ETF": "📑",
        "проблема": "⚠️", "взлом": "🔓", "атака": "🛑"
    }

    for word, emo in emoji_dict.items():
        if word.lower() in text.lower():
            text += f" {emo}"
    return text

async def fetch_news():
    """Получает новости из RSS, переводит и отправляет в Telegram"""
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        news_id = entry.link  # Уникальный ID новости (ссылка)
        if news_id in sent_news:
            continue  # Если уже отправляли — пропускаем

        sent_news.add(news_id)  # Добавляем в список отправленных
        title = entry.title
        link = entry.link
        summary = entry.summary if hasattr(entry, "summary") else "Без описания"

        translated_title = add_emojis(translate_text(title))
        translated_summary = add_emojis(translate_text(summary))

        message = f"📢 *{translated_title}*\n\n{translated_summary}\n[Читать далее]({link})"
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")

async def main():
    """Основной цикл"""
    while True:
        await fetch_news()
        await asyncio.sleep(60)  # Проверяем новости каждую минуту

if __name__ == "__main__":
    asyncio.run(main())
