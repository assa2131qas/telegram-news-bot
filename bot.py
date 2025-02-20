import time
import logging
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import Bot

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
NEWS_URL = "https://cryptoslate.com/news/"
LAST_NEWS_TITLE = None
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# === ФУНКЦИИ ===
def get_latest_news():
    """Парсим последнюю новость с CryptoSlate через requests"""
    try:
        response = requests.get(NEWS_URL, headers=HEADERS)
        if response.status_code != 200:
            logging.error(f"Ошибка запроса: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("a", class_="post-list-item")
        if not article:
            logging.info("Новостей нет или изменена структура страницы")
            return None
        
        title_tag = article.find("h2")
        title = title_tag.text.strip() if title_tag else ""
        img_tag = article.find("img")
        img_url = img_tag["src"] if img_tag else None
        
        logging.info(f"Найдена новость: {title}")
        return {"title": title, "img_url": img_url}
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return None


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    translated_text = GoogleTranslator(source="en", target="iw").translate(text)
    logging.info(f"Переведённый заголовок: {translated_text}")
    return translated_text


def send_to_telegram(news):
    """Отправляем новость в Telegram"""
    bot = Bot(token=TOKEN)
    
    title_he = translate_to_hebrew(news["title"])
    message = f"<b>{title_he}</b>"
    
    try:
        if news["img_url"]:
            bot.send_photo(chat_id=CHANNEL_ID, photo=news["img_url"], caption=message, parse_mode="HTML")
        else:
            bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML")
        logging.info(f"Опубликована новость: {news['title']}")
    except Exception as e:
        logging.error(f"Ошибка при отправке новости: {e}")


if __name__ == "__main__":
    LAST_NEWS_TITLE = None
    while True:
        news = get_latest_news()
        if news and news["title"] != LAST_NEWS_TITLE:
            send_to_telegram(news)
            LAST_NEWS_TITLE = news["title"]
        else:
            logging.info("Новостей нет, проверяем снова через 5 минут")
        time.sleep(300)  # Проверяем новости каждые 5 минут

