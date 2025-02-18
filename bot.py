import time
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import Bot

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
NEWS_URL = "https://ru.investing.com/news/cryptocurrency-news"
LAST_NEWS_TITLE = None

# === ФУНКЦИИ ===
def get_latest_news():
    """Парсим последнюю новость с Investing.com"""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(NEWS_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    article = soup.find("article")
    if not article:
        print("[LOG] Новых новостей нет")
        return None
    
    title = article.find("a").text.strip()
    img_tag = article.find("img")
    img_url = img_tag["src"] if img_tag else None
    
    return {"title": title, "img_url": img_url}


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    return GoogleTranslator(source="ru", target="iw").translate(text)


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
        print(f"[LOG] Опубликована новость: {news['title']}")
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке новости: {e}")


if __name__ == "__main__":
    LAST_NEWS_TITLE = None
    while True:
        news = get_latest_news()
        if news and news["title"] != LAST_NEWS_TITLE:
            send_to_telegram(news)
            LAST_NEWS_TITLE = news["title"]
        else:
            print("[LOG] Новых новостей нет, проверяем снова через 5 минут")
        time.sleep(300)  # Проверяем новости каждые 5 минут
