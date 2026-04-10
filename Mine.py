# meta developer: @tordkor
# meta banner: https://i.imgur.com/mineevo.png

from .. import loader, utils
import asyncio

@loader.tds
class MineEvoAutoMod(loader.Module):
    """Автосбор шахт для @mineEvo бота"""
    
    strings = {
        "name": "MineEvoAuto",
        "started": "✅ Автосбор mineEvo запущен",
        "stopped": "❌ Автосбор mineEvo остановлен",
        "collected": "💎 Собрал ресурсы!"
    }
    
    def __init__(self):
        self.running = False
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    @loader.command()
    async def start(self, message):
        """Запустить автосбор"""
        self.running = True
        await utils.answer(message, self.strings["started"])
        asyncio.create_task(self._watch_mineevo())
    
    @loader.command()
    async def stop(self, message):
        """Остановить автосбор"""
        self.running = False
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        """Слушает сообщения от mineEvo"""
        async for dialog in self.client.iter_dialogs():
            if dialog.entity.username == "mineEvo":
                chat_id = dialog.id
                break
        else:
            return
        
        async for message in self.client.iter_messages(chat_id, limit=1):
            last_msg_id = message.id
        
        while self.running:
            await asyncio.sleep(3)
            
            async for msg in self.client.iter_messages(chat_id, min_id=last_msg_id, limit=10):
                last_msg_id = msg.id
                
                if msg.text and ("копание завершено" in msg.text.lower() or "собери ресурсы" in msg.text.lower()):
                    if msg.reply_markup:
                        for row in msg.reply_markup.rows:
                            for button in row.buttons:
                                if "собрать" in button.text.lower():
                                    await msg.click(0)  # кликаем первую кнопку
                                    print(self.strings["collected"])
                                    await asyncio.sleep(2)
                                    break
