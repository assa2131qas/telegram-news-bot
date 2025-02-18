import requests
import asyncio
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher
from aiogram.types import InputMediaPhoto
from datetime import datetime, timedelta

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
CHANNEL_NAME = "Efasfsa"
CHANNEL_LINK = "https://t.me/fewf323wwdw"

# Источники новостей
CRYPTO_NEWS_URL = "https://ru.investing.com/news/cryptocurrency-news"
FOREX_EVENTS_URL = "https://www.forexfactory.com/calendar"
HEADERS = {"User-Agent": "Mozilla/5.0"}

bot = Bot(token=TOKEN)
dp = Dispatcher()

sent_news = set()

# === Словарь сокращений ===
event_translations = {
    "GDP": "תמ\"ג (תוצר מקומי גולמי)",
    "CPI": "מדד המחירים לצרכן",
    "Unemployment Rate": "שיעור האבטלה",
    "FOMC Statement": "הצהרת הוועדה הפדרלית",
    "Interest Rate Decision": "החלטת ריבית",
    "Retail Sales": "מכירות קמעонуаיות",
    "NFP": "דו\"ח התעסוקה בארה\"ב",
    "PMI": "מדד מנהלי הרכש",
    "Inflation Rate": "שיעור האינפלציה"
}

def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        print(f"⚠️ Ошибка перевода: {e}")
        return text  # Возвращаем оригинальный текст при ошибке

def get_crypto_news():
    try:
        response = requests.get(CRYPTO_NEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        articles = soup.find_all("article", class_="js-article-item")[:5]

        for article in articles:
            try:
                title = article.find("a", class_="title").get_text(strip=True)
                summary = article.find("p", class_="text").get_text(strip=True)
                img_tag = article.find("img")
                link_tag = article.find("a", class_="title")

                if link_tag and "href" in link_tag.attrs:
                    link = "https://ru.investing.com" + link_tag["href"]
                else:
                    link = CRYPTO_NEWS_URL

                img_url = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else None

                translated_title = translate_text(title)
                translated_summary = translate_text(summary)

                news_list.append({
                    "title": translated_title,
                    "summary": translated_summary,
                    "img": img_url,
                    "link": link
                })

            except AttributeError:
                continue  

        return news_list
    except Exception as e:
        print(f"❌ Ошибка получения крипто-новостей: {e}")
        return []

async def fetch_crypto_news():
    news = get_crypto_news()
    
    for article in news:
        news_id = article["title"]
        if news_id in sent_news:
            continue  

        sent_news.add(news_id)
        text = f"📰 *{article['title']}*\n📊 {article['summary']}\n\n" \
               f"[Читать далее]({article['link']})\n\n" \
               f"____________\n[{CHANNEL_NAME}]({CHANNEL_LINK})"

        try:
            if article["img"]:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=article["img"], caption=text, parse_mode="Markdown")
            else:
                await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Ошибка отправки новости в Telegram: {e}")

def get_forex_events():
    try:
        crypto_response = requests.get(CRYPTO_NEWS_URL, headers=HEADERS)
        forex_response = requests.get(FOREX_EVENTS_URL, headers=HEADERS)

