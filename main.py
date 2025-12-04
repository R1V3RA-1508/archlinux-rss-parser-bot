import feedparser
from html_to_markdown import convert
from datetime import datetime
import logging
import sys
import asyncio
from dotenv import load_dotenv
from os import getenv

from aiogram import Bot, Dispatcher


def ekran(string):
    new = (
        string.replace("<p>", "")
        .replace("</p>", "")
        .replace("<ul>", "")
        .replace("</ul>", "")
        .replace("<li>", "- ")
        .replace("</li>", "")
        .replace("<h1>", "")
        .replace("</h1>", "")
        .replace("<h2>", "")
        .replace("</h2>", "")
        .replace("<h3>", "")
        .replace("</h3>", "")
    )
    return new


class Database:
    def __init__(self):
        with open("sent.txt", "a", encoding="utf-8"):
            pass
        logging.debug("sent.txt создан, если его нет")

    def commit_news(self, id):
        with open("sent.txt", "a", encoding="utf-8") as f:
            f.write(f"{id}\n")
            logging.debug(f'В sent.txt записана новость с айди "{id}"')

    def check_news(self, id):
        with open("sent.txt", "r", encoding="utf-8") as f:
            sent_txt = f.read()
        if id in sent_txt:
            return True
        else:
            return False


class Parser:
    def __init__(self):
        url = "https://archlinux.org/feeds/packages/added"  # "https://archlinux.org/feeds/news"
        feed = feedparser.parse(url)
        self.url = url
        self.feed = feed
        self.db = Database()

    def get_news(self):
        news_list = []
        for i in self.feed.get("entries"):
            if not self.db.check_news(i.id):
                dt = datetime.strptime(i.published, "%a, %d %b %Y %H:%M:%S %z")
                pubtime = datetime.strftime(dt, "%d.%m.%Y %H:%M %Z")
                news_list.append(
                    {
                        "title": i.title,
                        "summary": ekran(i.summary),
                        "category": i.category,
                        "pubtime": pubtime,
                        "link": i.link,
                        "id": i.id,
                    }
                )
                # self.db.commit_news(i.id)
        return news_list


class BotS:
    def __init__(self) -> None:
        load_dotenv()
        self.TOKEN = getenv("token")
        self.CHANNEL_ID = getenv("channel_id")
        self.dp = Dispatcher()
        self.parser = Parser()
        self.bot = Bot(token=self.TOKEN)
        self.db = Database()

    async def send(self):
        news = self.parser.get_news()
        for n in news:
            await self.bot.send_message(
                text=f"""
Новый пакет в AUR:\n\
<b>{n.get("title")}</b>\n\n\
{n.get("summary")}\n\n\
Категория: <b>{n.get("category")}</b>\n\
Ссылка: <a href="{n.get("link")}">*тык*</a>\n\
Время публикации: {n.get("pubtime")}
""",
                chat_id=self.CHANNEL_ID,
                parse_mode="HTML",
            )
            logging.debug("Отправлена новость: " + n["title"])
            self.db.commit_news(n["id"])
            await asyncio.sleep(3)

    async def periodic_sending(self):
        while True:
            try:
                await self.send()
            except Exception as e:
                logging.error(f"Ошибка: {e}")
            await asyncio.sleep(60)


async def main():
    bot_instance = BotS()
    asyncio.create_task(bot_instance.periodic_sending())
    await bot_instance.dp.start_polling(bot_instance.bot)
    await bot_instance.send()
    while True:
        await asyncio.sleep(300)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(message)s", level=logging.DEBUG, stream=sys.stdout
    )
    asyncio.run(main())
