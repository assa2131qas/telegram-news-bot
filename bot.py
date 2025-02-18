import requests
import asyncio
import logging
import feedparser
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from datetime import datetime, timedelta

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
CHANNEL_NAME = "CryptoShuk"
CHANNEL_LINK = "https://t.me/CryptoShuk"

CRYPTO_NEWS_RSS = "https://cryptopanic.com/news/rss/"  # RSS-канал CryptoPanic
bot = Bot(token=TOKEN)
dp = Dispatcher()

sent_news = set()  # Хранение уже отправленных новостей

# === ФУНКЦИЯ ПЕРЕВОДА ===
def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        logging.error(f"Ошибка перевода: {e}")
        return text  # Если ошибка перевода, возвращаем оригинал

# === ПАРСИНГ НОВОСТЕЙ С ПРОВЕРКОЙ ВРЕМЕНИ ===
def get_crypto_news():
    try:
        feed = feedparser.parse(CRYPTO_NEWS_RSS)
        news_list = []

        for entry in feed.entries[:5]:  # Берём только 5 последних новостей
            title = entry.title
            summary = entry.summary
            link = entry.link
            published_time = entry.published_parsed

            news_time = datetime(*published_time[:6])  # Конвертация времени новости
            time_diff = datetime.utcnow() - news_time

            if time_diff > timedelta(hours=2):  # Пропускаем новости старше 2 часов
                logging.info(f"⏳ Пропущена старая новость ({time_diff}): {title}")
                continue

            translated_title = translate_text(title)
            translated_summary = translate_text(summary)

            news_list.append({
                "title": translated_title,
                "summary": translated_summary,
                "link": link,
                "time": news_time
            })

        logging.info(f"✅ Найдено {len(news_list)} новых статей.")
        return news_list

    except Exception as e:
        logging.error(f"❌ Ошибка получения новостей: {e}")
        return []

# === ОТПРАВКА НОВОСТЕЙ В TELEGRAM ===
async def send_crypto_news():
    news = get_crypto_news()
    
    if not news:
        logging.info("🔎 Проверка завершена: новых новостей нет.")
        return

    for article in news:
        news_id = article["title"]
        if news_id in sent_news:
            logging.info(f"🔄 Новость уже отправлена: {news_id}")
            continue  

        sent_news.add(news_id)

        text = f"📰 *{article['title']}*\n📊 {article['summary']}\n\n" \
               f"[Читать далее]({article['link']})\n\n" \
               f"____________\n[{CHANNEL_NAME}]({CHANNEL_LINK})"

        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.MARKDOWN)
            logging.info(f"📤 Отправлена новость: {article['title']}")

        except Exception as e:
            logging.error(f"❌ Ошибка отправки новости в Telegram: {e}")

# === ГЛАВНАЯ ФУНКЦИЯ ===
async def main():
    while True:
        await send_crypto_news()
        await asyncio.sleep(300)  # Проверка новостей каждые 5 минут

if __name__ == "__main__":
    asyncio.run(main())
