import time
import logging
import random
import requests
from bs4 import BeautifulSoup
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
NEWS_URL = "https://decrypt.co/news"
LAST_NEWS_TITLE = None
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

# === ФУНКЦИИ ===
def get_news(last_hours=2):
    """Парсим новости с Decrypt за последние `last_hours` часов"""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        time.sleep(random.uniform(1, 3))  # Добавляем случайную задержку
        response = requests.get(NEWS_URL, headers=headers)
        if response.status_code != 200:
            logging.error(f"Ошибка запроса: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("a", class_="py-4")  # Ищем блоки новостей
        if not articles:
            logging.info("Новостей нет или изменена структура страницы")
            return []
        
        news_list = []
        for article in articles:
            title_tag = article.find("h2")
            title = title_tag.text.strip() if title_tag else ""
            img_tag = article.find("img")
            img_url = img_tag["src"] if img_tag else None
            
            news_list.append({"title": title, "img_url": img_url})
        
        logging.info(f"Найдено {len(news_list)} новостей")
        return news_list
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return []


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
    # При первом запуске проверяем новости за последние 2 часа
    news_list = get_news(last_hours=2)
    for news in news_list:
        send_to_telegram(news)
        time.sleep(3)
    
    LAST_NEWS_TITLE = news_list[0]["title"] if news_list else None
    
    # Дальше проверяем новости каждые 5 минут
    while True:
        news_list = get_news(last_hours=1)
        if news_list and news_list[0]["title"] != LAST_NEWS_TITLE:
            send_to_telegram(news_list[0])
            LAST_NEWS_TITLE = news_list[0]["title"]
        else:
            logging.info("Новостей нет, проверяем снова через 5 минут")
        time.sleep(300)  # Проверяем новости каждые 5 минут
