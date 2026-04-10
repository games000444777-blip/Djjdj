from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

async def auto_mineevo(client: Client):
    print("AutoMineEvo запущен — жду сбор")

    @client.on_message(filters.user("mineEvo"))
    async def handle(c: Client, m: Message):
        text = m.text or ""
        if "копание завершено" in text.lower() or "собери ресурсы" in text.lower():
            print("Обнаружен сбор — кликаю...")
            await asyncio.sleep(1.5)
            if m.reply_markup:
                for row in m.reply_markup.inline_keyboard:
                    for button in row:
                        if "собрать" in button.text.lower():
                            try:
                                await m.click(button.text)
                                print("Собрал ресурсы!")
                                return
                            except:
                                pass

def setup(client: Client):
    asyncio.create_task(auto_mineevo(client))
