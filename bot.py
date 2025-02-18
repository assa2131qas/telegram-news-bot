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
    "Retail Sales": "מכירות קמעונאיות",
    "NFP": "דו\"ח התעסוקה בארה\"ב",
    "PMI": "מדד מנהלי הרכש",
    "Inflation Rate": "שיעור האינפלציה"
}

def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        return f"Ошибка перевода: {e}"

def get_crypto_news():
    response = requests.get(CRYPTO_NEWS_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []
    articles = soup.find_all("article", class_="js-article-item")[:5]

    for article in articles:
        try:
            title = article.find("a", class_="title").get_text(strip=True)
            summary = article.find("p", class_="text").get_text(strip=True)
            img_tag = article.find("img")
            link = article.find("a", class_="title")["href"]

            img_url = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else None

            translated_title = translate_text(title)
            translated_summary = translate_text(summary)

            news_list.append({"title": translated_title, "summary": translated_summary, "img": img_url, "link": link})

        except AttributeError:
            continue  # Пропускаем ошибочные строки

    return news_list

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

        if article["img"]:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=article["img"], caption=text, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")

def get_forex_events():
    """Парсит экономический календарь с ForexFactory и логирует найденные события."""
    response = requests.get(FOREX_EVENTS_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    events = {}

    table = soup.find("table", class_="calendar__table")

    if not table:
        print("❌ Ошибка: Не найдена таблица с событиями.")
        return {}

    rows = table.find_all("tr", class_="calendar__row")

    for row in rows:
        try:
            time = row.find("td", class_="calendar__time").text.strip()
            currency = row.find("td", class_="calendar__currency").text.strip()
            event = row.find("td", class_="calendar__event").text.strip()
            
            for eng_term, hebrew_translation in event_translations.items():
                if eng_term in event:
                    event = event.replace(eng_term, hebrew_translation)

            day = row.find("td", class_="calendar__date").text.strip()

            if day not in events:
                events[day] = []

            event_text = f"🕒 {time} – {event} ({currency})"
            events[day].append(event_text)

            print(f"✅ Добавлено событие: {event_text}")

        except AttributeError as e:
            print(f"⚠️ Пропущена строка из-за ошибки: {e}")
            continue

    return events

async def send_weekly_forex_events():
    events = get_forex_events()
    
    message = "📆 *אירועים כלכליים לשבוע הקרוב*\n\n"
    for day, event_list in events.items():
        message += f"📍 *{day}*\n" + "\n".join(event_list) + "\n\n"

    message += f"____________\n[{CHANNEL_NAME}]({CHANNEL_LINK})"
    
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")

async def send_daily_forex_events():
    events = get_forex_events()
    
    today = datetime.utcnow().strftime("%b %d")  

    if today in events:
        message = f"📆 *אירועים כלכליים היום - {today}*\n\n"
        message += "\n".join(events[today]) + "\n\n"
        message += f"____________\n[{CHANNEL_NAME}]({CHANNEL_LINK})"
        
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")

async def weekly_task():
    while True:
        now = datetime.utcnow()
        next_saturday = now + timedelta(days=(5 - now.weekday()) % 7)
        target_time = datetime(next_saturday.year, next_saturday.month, next_saturday.day, 18, 0)
        await asyncio.sleep((target_time - now).total_seconds())
        await send_weekly_forex_events()

async def daily_task():
    while True:
        now = datetime.utcnow()
        target_time = datetime(now.year, now.month, now.day, 6, 10)  # Исправлено на 06:10 UTC
        await asyncio.sleep((target_time - now).total_seconds() % 86400)
        await send_daily_forex_events()

async def main():
    asyncio.create_task(weekly_task())
    asyncio.create_task(daily_task())
    while True:
        await fetch_crypto_news()
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
