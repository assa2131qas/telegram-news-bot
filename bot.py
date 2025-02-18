import requests
import feedparser
import asyncio
import emoji
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher
from aiogram.types import InputMediaPhoto

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"   # Вставь токен из BotFather
CHANNEL_ID = "-1002447063110"  # Или Chat ID, если канал приватный
URL = "https://ru.investing.com/news/cryptocurrency-news"
HEADERS = {"User-Agent": "Mozilla/5.0"}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список отправленных новостей (чтобы не дублировать)
sent_news = set()

def translate_text(text):
    """Переводит текст на иврит через Google Translate"""
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        return f"Ошибка перевода: {e}"

def add_emojis(text):
    """Добавляет эмодзи в зависимости от содержания новости"""
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

def get_news():
    """Парсит новости с Investing.com, включая картинки"""
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []
    articles = soup.find_all("article", class_="js-article-item")[:5]  # Берём 5 свежих новостей

    for article in articles:
        title = article.find("a", class_="title").get_text(strip=True)  # Заголовок
        summary = article.find("p", class_="text").get_text(strip=True)  # Краткое описание
        img_tag = article.find("img")  # Находим тег <img>

        if img_tag and "data-src" in img_tag.attrs:
            img_url = img_tag["data-src"]  # Получаем ссылку на картинку
        else:
            img_url = None  # Если нет картинки

        # Перевод заголовка и описания на иврит + добавление эмодзи
        translated_title = add_emojis(translate_text(title))
        translated_summary = add_emojis(translate_text(summary))

        news_list.append({"title": translated_title, "summary": translated_summary, "img": img_url})

    return news_list

async def fetch_news():
    """Получает новости и отправляет в Telegram"""
    news = get_news()
    
    for article in news:
        news_id = article["title"]  # Уникальный ID (заголовок)
        if news_id in sent_news:
            continue  # Если уже отправляли — пропускаем

        sent_news.add(news_id)  # Добавляем в список отправленных
        text = f"📰 *{article['title']}*\n📊 {article['summary']}"

        if article["img"]:  # Если есть картинка, отправляем с фото
            await bot.send_photo(chat_id=CHANNEL_ID, photo=article["img"], caption=text, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")

async def main():
    """Основной цикл"""
    while True:
        await fetch_news()
        await asyncio.sleep(300)  # Проверяем новости каждые 5 минут

if __name__ == "__main__":
    asyncio.run(main())
