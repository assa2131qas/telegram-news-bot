import time
import logging
import random
import requests
import asyncio
import re
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
NEWS_URL = "https://decrypt.co/news"
LAST_NEWS_TITLE = None
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

# Список разрешённых категорий
ALLOWED_CATEGORIES = {"Coins", "Law and Order", "Business", "Technology", "Gaming"}
CATEGORY_CLASS = "text-cc-pink-2"

# === ФУНКЦИИ ===
def get_news():
    """Парсим последние новости с Decrypt, исключая курсы криптовалют и определяя категорию"""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        time.sleep(random.uniform(1, 3))  # Добавляем случайную задержку
        response = requests.get(NEWS_URL, headers=headers)
        if response.status_code != 200:
            logging.error(f"Ошибка запроса: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
        
        if not articles:
            logging.info("Новостей нет или изменена структура страницы")
            return []
        
        news_list = []
        for article in articles:
            category_tag = article.find("span", class_=CATEGORY_CLASS)
            category = category_tag.text.strip() if category_tag else "Без категории"
            
            if category not in ALLOWED_CATEGORIES:
                logging.info(f"Пропускаем новость: {category} не в списке разрешённых")
                continue
            
            title_tag = article.find("h3") or article.find("h2")
            title = title_tag.text.strip() if title_tag else ""
            
            summary_tag = article.find("p")
            summary = summary_tag.text.strip() if summary_tag else ""
            
            img_tag = article.find("img")
            img_url = img_tag["src"] if img_tag else None
            
            # Фильтр: убираем новости, состоящие только из чисел (цены криптовалют)
            if not title or re.match(r'^[\d.,$€£]+$', title):
                logging.info(f"Пропускаем нерелевантную новость: {title}")
                continue
            
            logging.info(f"Найдена новость: [{category}] {title} | Описание: {summary} | Изображение: {img_url}")
            news_list.append({"category": category, "title": title, "summary": summary, "img_url": img_url})
        
        return news_list
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return []


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    translated_text = GoogleTranslator(source="en", target="iw").translate(text)
    logging.info(f"Переведённый текст: {translated_text}")
    return translated_text


async def send_to_telegram(news):
    """Отправляем новость в Telegram"""
    bot = Bot(token=TOKEN)
    category_he = translate_to_hebrew(news["category"])
    title_he = translate_to_hebrew(news["title"])
    summary_he = translate_to_hebrew(news["summary"]) if news["summary"] else ""
    message = f"<b>{category_he}</b>\n<b>{title_he}</b>\n\n{summary_he}"
    
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
    
    # При первом запуске проверяем последние новости
    news_list = get_news()
    for news in reversed(news_list):  # Публикуем от старых к новым
        loop.run_until_complete(send_to_telegram(news))
        time.sleep(3)
    
    LAST_NEWS_TITLE = news_list[0]["title"] if news_list else None
    
    # Дальше проверяем новости каждые 5 минут
    while True:
        news_list = get_news()
        if news_list and news_list[0]["title"] != LAST_NEWS_TITLE:
            loop.run_until_complete(send_to_telegram(news_list[0]))
            LAST_NEWS_TITLE = news_list[0]["title"]
        else:
            logging.info("Новостей нет, проверяем снова через 5 минут")
        time.sleep(300)  # Проверяем новости каждые 5 минут
