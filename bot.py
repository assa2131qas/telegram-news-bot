import requests
import asyncio
import logging
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher
from datetime import datetime, timedelta

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === НАСТРОЙКИ ===
TOKEN = "7414890925:AAFxyXC2gGMMxu5Z3KVw5BVvYJ75Db2m85c"
CHANNEL_ID = "-1002447063110"
CHANNEL_NAME = "CryptoShuk"
CHANNEL_LINK = "https://t.me/CryptoShuk"

CRYPTO_NEWS_URL = "https://ru.investing.com/news/cryptocurrency-news"
HEADERS = {"User-Agent": "Mozilla/5.0"}

bot = Bot(token=TOKEN)
dp = Dispatcher()
sent_news = set()  # Хранение уже отправленных новостей

# === ФУНКЦИЯ ПЕРЕВОДА ===
def translate_text(text):
    try:
        return GoogleTranslator(source="auto", target="iw").translate(text)
    except Exception as e:
        logging.error(f"Ошибка перевода: {e}")
        return text  # Если ошибка перевода, возвращаем оригинал

# === ПАРСИНГ НОВОСТЕЙ С ПРОВЕРКОЙ ВРЕМЕНИ ===
def get_crypto_news():
    try:
        response = requests.get(CRYPTO_NEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        articles = soup.find_all("article", class_="js-article-item")[:5]

        for article in articles:
            try:
                title_tag = article.find("a", class_="title")
                summary_tag = article.find("p", class_="text")
                time_tag = article.find("span", class_="date")  # Время публикации
                img_tag = article.find("img")

                if title_tag and summary_tag and time_tag:
                    title = title_tag.get_text(strip=True)
                    summary = summary_tag.get_text(strip=True)
                    time_text = time_tag.get_text(strip=True)
                    link = "https://ru.investing.com" + title_tag["href"]
                    img_url = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else None

                    # === Проверяем возраст новости ===
                    news_time = parse_time(time_text)
                    time_diff = datetime.utcnow() - news_time
                    
                    if time_diff > timedelta(hours=2):  # Игнорируем новости старше 2 часов
                        logging.info(f"⏳ Пропущена новость (старая, {time_diff}): {title}")
                        continue  

                    translated_title = translate_text(title)
                    translated_summary = translate_text(summary)

                    news_list.append({
                        "title": translated_title,
                        "summary": translated_summary,
                        "img": img_url,
                        "link": link,
                        "time": news_time
                    })

            except AttributeError as e:
                logging.warning(f"Пропущена новость из-за ошибки: {e}")
                continue  

        logging.info(f"✅ Найдено {len(news_list)} новых статей.")
        return news_list

    except Exception as e:
        logging.error(f"❌ Ошибка получения новостей: {e}")
        return []

# === ПАРСИНГ ВРЕМЕНИ ПУБЛИКАЦИИ ===
def parse_time(time_text):
    """
    Преобразует текст времени новости в объект datetime.
    Например: "1 час назад", "42 мин. назад", "17 фев 2024".
    """
    now = datetime.utcnow()

    if "мин" in time_text:
        minutes = int(time_text.split()[0])
        return now - timedelta(minutes=minutes)
    elif "час" in time_text:
        hours = int(time_text.split()[0])
        return now - timedelta(hours=hours)
    else:
        return now  # Если формат неизвестен, считаем новость свежей

# === ОТПРАВКА НОВОСТЕЙ В TELEGRAM ===
async def send_crypto_news():
    news = get_crypto_news()
    
    if not news:
        logging.info("🔎 Проверка завершена: новых новостей нет.")
        return

    for article in news:
        news_id = article["title"]
        if news_id in sent_news:
            logging.info(f"🔄 Новость уже отправлена: {news_id}")
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

            logging.info(f"📤 Отправлена новость: {article['title']}")

        except Exception as e:
            logging.error(f"❌ Ошибка отправки новости в Telegram: {e}")

# === ГЛАВНАЯ ФУНКЦИЯ ===
async def main():
    while True:
        await send_crypto_news()
        await asyncio.sleep(300)  # Проверка новостей каждые 5 минут

if __name__ == "__main__":
    asyncio.run(main())
