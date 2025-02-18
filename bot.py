import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from telegram import Bot

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
NEWS_URL = "https://ru.investing.com/news/cryptocurrency-news"

# === ФУНКЦИИ ===
def get_latest_news():
    """Парсим последнюю новость с Investing.com"""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(NEWS_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    article = soup.find("article")
    if not article:
        return None
    
    title = article.find("a").text.strip()
    link = "https://ru.investing.com" + article.find("a")["href"]
    img_tag = article.find("img")
    img_url = img_tag["src"] if img_tag else None
    
    return {"title": title, "link": link, "img_url": img_url}


def translate_to_hebrew(text):
    """Переводим текст на иврит"""
    translator = Translator()
    return translator.translate(text, src="ru", dest="iw").text


def send_to_telegram(news):
    """Отправляем новость в Telegram"""
    bot = Bot(token=TOKEN)
    
    title_he = translate_to_hebrew(news["title"])
    message = f"<b>{title_he}</b>\n\n🔗 <a href='{news['link']}'>Читать полностью</a>"
    
    if news["img_url"]:
        bot.send_photo(chat_id=CHANNEL_ID, photo=news["img_url"], caption=message, parse_mode="HTML")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML")


if __name__ == "__main__":
    news = get_latest_news()
    if news:
        send_to_telegram(news)
