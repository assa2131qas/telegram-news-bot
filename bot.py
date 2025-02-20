import time
import logging
import shutil
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import Bot

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# === УСТАНОВКА CHROMIUM ===
logging.info("Устанавливаем Chromium...")
os.system("apt-get update && apt-get install -y chromium")

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
NEWS_URL = "https://ru.investing.com/news/cryptocurrency-news"
LAST_NEWS_TITLE = None

# === Проверяем, установлен ли Chrome ===
CHROME_PATH = shutil.which("chromium") or shutil.which("chromium-browser") or "/usr/bin/chromium"
if not CHROME_PATH:
    logging.error("Chromium не найден! Убедитесь, что он установлен.")
    exit(1)

# === НАСТРОЙКИ SELENIUM ===
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = CHROME_PATH

# === ФУНКЦИИ ===
def get_latest_news():
    """Парсим последнюю новость с Investing.com через Selenium"""
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(NEWS_URL)
        time.sleep(5)  # Ждём загрузку страницы
        
        page_source = driver.page_source
        driver.quit()
        
        # Логируем часть HTML для отладки
        logging.info(f"HTML страницы: {page_source[:1000]}")
        
        soup = BeautifulSoup(page_source, "html.parser")
        article = soup.find("article")
        if not article:
            logging.info("Новостей нет или изменена структура страницы")
            return None
        
        title = article.find("a").text.strip()
        img_tag = article.find("img")
        img_url = img_tag["src"] if img_tag else None
        
        logging.info(f"Найдена новость: {title}")
        return {"title": title, "img_url": img_url}
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return None


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    translated_text = GoogleTranslator(source="ru", target="iw").translate(text)
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
