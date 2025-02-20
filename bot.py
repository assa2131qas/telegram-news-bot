import time
import logging
import asyncio
import feedparser
from deep_translator import GoogleTranslator
from telegram import Bot
from datetime import datetime, timedelta

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
RSS_FEED_URL = "https://cryptoslate.com/feed/"
POSTED_NEWS = set()

# === ФУНКЦИИ ===
def get_news():
    """Получаем новости из RSS Feed"""
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            logging.warning("Ошибка при разборе RSS: нет записей")
            return []

        news_list = []
        for entry in feed.entries:
            title = entry.title
            summary = entry.summary if 'summary' in entry else ""
            img_url = None

            # Извлечение изображения
            if 'media_content' in entry and entry.media_content:
                img_url = entry.media_content[0]['url']
            elif 'enclosure' in entry and 'url' in entry.enclosure:
                img_url = entry.enclosure['url']

            logging.info(f"Найдена новость: {title} | Изображение: {img_url}")
            news_list.append({"title": title, "summary": summary, "img_url": img_url})

        logging.info(f"Всего новостей в RSS: {len(news_list)}")
        return news_list
    except Exception as e:
        logging.error(f"Ошибка парсинга RSS: {e}")
        return []


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    try:
        translated_text = GoogleTranslator(source="en", target="iw").translate(text)
        logging.info(f"Переведённый текст: {translated_text}")
        return translated_text
    except Exception as e:
        logging.error(f"Ошибка перевода: {e}")
        return text  # Возвращаем оригинальный текст при ошибке


async def send_to_telegram(news):
    """Отправляем новость в Telegram"""
    bot = Bot(token=TOKEN)
    title_he = translate_to_hebrew(news["title"])
    summary_he = translate_to_hebrew(news["summary"]) if news["summary"] else ""

    message = f"<b>{title_he}</b>\n\n{summary_he}"

    try:
        if news["img_url"]:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=news["img_url"], caption=message[:1024], parse_mode="HTML")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML")

        logging.info(f"Опубликована новость: {news['title']}")
    except Exception as e:
        logging.error(f"Ошибка при отправке новости: {e}")


async def main():
    global POSTED_NEWS
    while True:
        news_list = get_news()

        for news in reversed(news_list):
            if news["title"] not in POSTED_NEWS:
                await send_to_telegram(news)
                POSTED_NEWS.add(news["title"])
                time.sleep(3)

        logging.info("Новостей нет, проверяем снова через 10 минут")
        await asyncio.sleep(600)  # Проверяем новости каждые 10 минут


if __name__ == "__main__":
    asyncio.run(main())
