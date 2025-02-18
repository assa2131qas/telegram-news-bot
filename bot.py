import feedparser
import asyncio
import logging
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


# RSS-канал CryptoPanic (главные новости)
RSS_URL = "https://cryptopanic.com/news/rss/"

# Telegram Bot
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список отправленных новостей
sent_news = set()

def parse_time(time_text):
    """
    Преобразует текст времени новости в объект datetime.
    Например: "1 час назад", "42 мин. назад", "17 фев 2024".
    """
    now = datetime.utcnow()

    if "minute" in time_text:
        minutes = int(time_text.split()[0])
        return now - timedelta(minutes=minutes)
    elif "hour" in time_text:
        hours = int(time_text.split()[0])
        return now - timedelta(hours=hours)
    else:
        return now  # Если формат неизвестен, считаем новость свежей

async def fetch_cryptopanic_news():
    """ Получение новостей из CryptoPanic RSS """
    feed = feedparser.parse(RSS_URL)
    new_articles = []

    for entry in feed.entries[:10]:  # Берем 10 последних новостей
        title = entry.title
        summary = entry.summary if "summary" in entry else ""

        # Проверяем возраст новости
        news_time = parse_time(entry.published) if "published" in entry else datetime.utcnow()
        time_diff = datetime.utcnow() - news_time

        if time_diff > timedelta(hours=2):  # Фильтруем старые новости
            logging.info(f"⏳ Пропущена новость (старая, {time_diff}): {title}")
            continue  

        # Проверяем, было ли уже отправлено
        if title in sent_news:
            logging.info(f"🔄 Новость уже отправлена: {title}")
            continue  

        sent_news.add(title)  # Запоминаем отправленные новости

        # Формируем сообщение
        text = f"📰 *{title}*\n📖 {summary}\n\n" \
               f"____________\n[{CHANNEL_NAME}]({CHANNEL_LINK})"

        new_articles.append(text)

    return new_articles

async def send_news():
    """ Отправка новостей в Telegram """
    news_list = await fetch_cryptopanic_news()

    if not news_list:
        logging.info("🔎 Проверка завершена: новых новостей нет.")
    else:
        for news in news_list:
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=news, parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(3)  # Пауза между сообщениями
                logging.info(f"📤 Отправлена новость: {news.split('*')[1]}")  # Лог заголовка
            except Exception as e:
                logging.error(f"❌ Ошибка отправки сообщения: {e}")

async def main():
    """ Основной цикл работы бота """
    while True:
        await send_news()
        await asyncio.sleep(300)  # Проверяем каждые 5 минут

if __name__ == "__main__":
    logging.info("🚀 Бот запущен и проверяет новости!")
    asyncio.run(main())
