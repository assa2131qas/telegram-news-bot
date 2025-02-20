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
LAST_NEWS_TITLE = None

# === ФУНКЦИИ ===
def get_news():
    """Получаем новости из RSS Feed"""
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if 'entries' not in feed:
            logging.error("Ошибка при разборе RSS ленты")
            return []
        
        news_list = []
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        
        for entry in feed.entries:
            pub_date = datetime(*entry.published_parsed[:6])
            if pub_date < two_days_ago:
                continue
            
            title = entry.title
            summary = entry.summary if 'summary' in entry else ""
            img_url = None
            
            # Извлечение изображения
            if 'media_content' in entry and entry.media_content:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                        img_url = link['href']
                        break
            
            logging.info(f"Найдена новость: {title} | {summary} | {img_url}")
            news_list.append({"title": title, "summary": summary, "img_url": img_url})
        
        logging.info(f"Найдено {len(news_list)} новостей за последние 2 дня")
        return news_list
    except Exception as e:
        logging.error(f"Ошибка парсинга RSS: {e}")
        return []


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    translated_text = GoogleTranslator(source="en", target="iw").translate(text)
    logging.info(f"Переведённый текст: {translated_text}")
    return translated_text


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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    news_list = get_news()
    for news in reversed(news_list):  # Публикуем от старых к новым
        loop.run_until_complete(send_to_telegram(news))
        time.sleep(3)
    
    LAST_NEWS_TITLE = news_list[0]["title"] if news_list else None
    
    while True:
        news_list = get_news()
        if news_list and news_list[0]["title"] != LAST_NEWS_TITLE:
            loop.run_until_complete(send_to_telegram(news_list[0]))
            LAST_NEWS_TITLE = news_list[0]["title"]
        else:
            logging.info("Новостей нет, проверяем снова через 5 минут")
        time.sleep(300)  # Проверяем новости каждые 5 минут
